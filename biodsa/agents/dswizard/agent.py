"""
Proposed by:

Wang, Z., et al. (2025). Making Large Language Models Reliable Data Science Copilot for Biomedical Research. Nature Biomedical Engineering.
"""
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.state import CodeExecutionResult
from biodsa.agents.dswizard.state import DSWizardAgentState
from biodsa.sandbox.execution import ExecutionResults

from biodsa.tool_wrappers.code_exec_tool import CodeExecutionTool
from biodsa.agents.dswizard.analysis_plan_tool import AnalysisPlanTool

PLAN_AGENT_SYSTEM_PROMPT_TEMPLATE = """
You are an expert data analysis agent. Your job is to create a step-by-step analysis plan written in natural language to ensure it can be faithfully implemented as Python code.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.

You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
- print(statistical_test_output)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.

# Guidline:
1. You should first try to understand the user's question and then explore the available datasets by making `code_execution` tool calls to collect 
    - the necessary dataset schema information (table names, column names, data types, value ranges, etc.)
    - the availability of packages to be used
2. After you are confident, call the `create_analysis_plan` tool to create the analysis plan. The plan should contain (1) the steps to resolve the user's question and (2) the necessary quality control steps to assess the quality of the analysis results will be made by (1)
3. Review the completed analysis plan. If the plan does not cover all the necessary steps or have ambiguities about which parts of the dataset to use, you should go back to step 1 and repeat the process.
4. If the plan is complete, you can stop and just return your response. Your final response should be only a sentence
    "The analysis plan is complete."
without anything else to do.

# Available data:
You have access to the following data when executing the code:
{registered_datasets_str}

You are given:
1. A user request describing the data analysis task.
2. Tools to inspect the dataset schema and execute Python code snippets.
"""

CODE_AGENT_SYSTEM_PROMPT_TEMPLATE = """
You are a code generation agent. Your job is to convert a detailed, step-by-step ANALYSIS_PLAN into correct and complete Python code,
and then you can collect the code execution results to answer the user's question.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.

You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
- print(statistical_test_output)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.

# Guideline:
1. You should first review the ANALYSIS_PLAN and inspect feasibilities of the key steps in the plan.
2. If any specific step is not feasible, you should do more rounds of exporation with code execution to get the necessary information to complete the step.
3. After you get the necessary information to fix the step, go back to step 1 and repeat the process.
4. If you finally make sure all the analysis plan steps are feasible, you can make the final code execution and then return your answer to the user.

# Available data:
You have access to the following data when executing the code:
{registered_datasets_str}

You are given:
1. A user request describing the data analysis task.
2. A detailed, step-by-step ANALYSIS_PLAN that needs to be converted into correct and complete Python code.
3. Tools to execute Python code snippets and collect the code execution results.
"""

class DSWizardAgent(BaseAgent):
    name = "dswizard"    

    def __init__(
        self, 
        model_name: str, 
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        small_model_name: str = None, # a optional smaller model to help complete the analysis plan content
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        if small_model_name is None:
            self.small_model_name = self.model_name
            self.small_llm = self.llm
        else:
            self.small_model_name = small_model_name
            self.small_llm = self._get_model(
                api=self.api_type,
                model_name=self.small_model_name,
                api_key=self.api_key,
                endpoint=self.endpoint,
                **kwargs
            )

        self.agent_graph = self._create_agent_graph()
        # for debugging
        # graph_object = self.agent_graph.get_graph(xray=1)
        # graph_object.draw_mermaid_png(output_file_path="dswizard_graph.png")
    
    def _build_system_prompt_for_plan_agent(self):
        registered_datasets_str = "\n".join([f"- {dataset}" for dataset in self.registered_datasets])
        return PLAN_AGENT_SYSTEM_PROMPT_TEMPLATE.format(registered_datasets_str=registered_datasets_str)

    def _build_system_prompt_for_code_agent(self):
        registered_datasets_str = "\n".join([f"- {dataset}" for dataset in self.registered_datasets])
        return CODE_AGENT_SYSTEM_PROMPT_TEMPLATE.format(registered_datasets_str=registered_datasets_str)

    def _get_tools_for_plan_agent(self):
        tools = [CodeExecutionTool(sandbox=self.sandbox)]
        analysis_plan_tool = AnalysisPlanTool(llm=self.small_llm)
        tools.append(analysis_plan_tool)
        return tools

    def _get_tools_for_code_agent(self):
        tools = [CodeExecutionTool(sandbox=self.sandbox)]
        return tools

    def _get_all_tools(self):
        return self._get_tools_for_plan_agent() + self._get_tools_for_code_agent()

    def _plan_agent_node(self, state: DSWizardAgentState, config: RunnableConfig) -> DSWizardAgentState:
        messages = state.messages
        system_prompt = self._build_system_prompt_for_plan_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_plan_agent()
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        llm_with_tools = llm.bind_tools(tools)
        response = run_with_retry(llm_with_tools.invoke, arg=messages)
        return {
            "messages": [response],
        }

    def _code_agent_node(self, state: DSWizardAgentState, config: RunnableConfig) -> DSWizardAgentState:
        messages = state.messages
        analysis_plan = state.analysis_plan
        user_query = state.user_query

        system_prompt = self._build_system_prompt_for_code_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages + [HumanMessage(content=f"USER_QUERY: \n\n{user_query}"), HumanMessage(content=f"ANALYSIS_PLAN: \n\n{analysis_plan}")]
        tools = self._get_tools_for_code_agent()
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        llm_with_tools = llm.bind_tools(tools)
        response = run_with_retry(llm_with_tools.invoke, arg=messages)
        return {
            "messages": [response],
        }

    def _tool_node(self, state: DSWizardAgentState, config: RunnableConfig) -> DSWizardAgentState:
        messages = state.messages
        tools = self._get_all_tools()
        tool_dict = {tool.name: tool for tool in tools}

        tool_call = state.messages[-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        tool = tool_dict[tool_name]

        print(f"Executing tool: {tool_name} with input: {tool_input}")
        if tool_name == "create_analysis_plan":
            # prepare the context_str for the analysis plan tool
            context_str = "\n\n".join([f"{message.type}: \n\n{message.content}" for message in messages])
            tool_input["context_str"] = context_str
            tool_output = tool._run(**tool_input)
        else:
            tool_output = tool._run(**tool_input)

        # collect the results for the special tools
        code_result = None
        analysis_plan = None
        if tool_name == "code_execution":
            content = tool_output["stdout"]
            # update the code results
            code_result = CodeExecutionResult(
                code=tool_input["code"],
                console_output=tool_output["stdout"],
                running_time=tool_output["running_time"],
                peak_memory=tool_output["peak_memory_mb"],
            )
        elif tool_name == "create_analysis_plan":
            content = tool_output
            analysis_plan = tool_output
        else:
            content = tool_output

        response = ToolMessage(
            content=content,
            name=tool_name,
            tool_call_id=tool_call["id"]
        )
        output_dict = {"messages": [response]}

        # update with the special results
        if code_result is not None:
            existing_code_results = state.code_execution_results
            existing_code_results.append(code_result)
            output_dict["code_execution_results"] = existing_code_results

        if analysis_plan is not None:
            output_dict["analysis_plan"] = analysis_plan

        return output_dict

    def _should_continue_plan_agent(self, state: DSWizardAgentState) -> Literal["tool_node", "end"]:
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "tool_node"

    def _should_continue_code_agent(self, state: DSWizardAgentState) -> Literal["tool_node", "end"]:
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "tool_node"

    def _create_agent_graph(self, debug: bool = False):
        # plan agent workflow
        plan_agent_workflow = StateGraph(
            DSWizardAgentState,
            input=DSWizardAgentState,
            output=DSWizardAgentState
        )
        plan_agent_workflow.add_node("plan_agent_node", self._plan_agent_node)
        plan_agent_workflow.add_node("tool_node", self._tool_node)
        plan_agent_workflow.add_conditional_edges(
            "plan_agent_node",
            self._should_continue_plan_agent,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        plan_agent_workflow.add_edge("tool_node", "plan_agent_node")
        plan_agent_workflow.set_entry_point("plan_agent_node")
        plan_agent_workflow = plan_agent_workflow.compile(
            debug=debug,
            name="plan_agent_workflow"
        )

        # code agent workflow
        code_agent_workflow = StateGraph(
            DSWizardAgentState,
            input=DSWizardAgentState,
            output=DSWizardAgentState
        )
        code_agent_workflow.add_node("code_agent_node", self._code_agent_node)
        code_agent_workflow.add_node("tool_node", self._tool_node)
        code_agent_workflow.add_conditional_edges(
            "code_agent_node",
            self._should_continue_code_agent,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        code_agent_workflow.add_edge("tool_node", "code_agent_node")
        code_agent_workflow.set_entry_point("code_agent_node")
        code_agent_workflow = code_agent_workflow.compile(
            debug=debug,
            name="code_agent_workflow"
        )

        # main workflow
        workflow = StateGraph(
            DSWizardAgentState,
            input=DSWizardAgentState,
            output=DSWizardAgentState
        )
        workflow.add_node("plan_agent", plan_agent_workflow)
        workflow.add_node("code_agent", code_agent_workflow)
        workflow.add_edge("plan_agent", "code_agent")
        workflow.add_edge("code_agent", END)
        workflow.set_entry_point("plan_agent")
        workflow = workflow.compile(
            debug=debug,
            name=self.name
        )
        return workflow

    def generate(
        self,
        input_query: str,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Override the base method for generating the response.
        
        Args:
            input_query: The user query to process
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Extract input_query from kwargs
        if input_query is None:
            return [{"error": "input_query is required"}]
        
        try:
            all_results = []
            inputs = {
                "messages": [("user", input_query)],
                "user_query": input_query
            }
        
            # Invoke the agent graph and return the result
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode = ["values"],
                config={
                    "configurable": {
                        "model_kwargs": {
                            "max_completion_tokens": 5000,
                            "reasoning_effort": "minimal",
                            "temperature": 1.0
                        }
                    },
                    "recursion_limit": 20
                }
            ):
                if verbose:
                    last_message = chunk['messages'][-1]
                    print("-" * 100)
                    print(f"{last_message.type}: \n\n{last_message.content}\n\n")
                all_results.append(chunk)
            return all_results
            
        except Exception as e:
            print(f"Error streaming response: {e}")
            raise e

    def go(
        self,
        input_query: str,
        verbose: bool = True
    ) -> ExecutionResults:
        """
        A function to execute the agent and return the execution results.
        
        Args:
            input_query: The user query to process
        """
        results = self.generate(input_query, verbose=verbose)
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        code_execution_results = self._format_code_execution_results(final_state['code_execution_results'])
        final_response = final_state['messages'][-1].content

        return ExecutionResults(
            sandbox=self.sandbox,
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response
        )