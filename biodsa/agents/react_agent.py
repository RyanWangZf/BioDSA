import re
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.state import AgentState, CodeExecutionResult
from biodsa.sandbox.execution import ExecutionResults
from biodsa.tools.code_exec_tool import CodeExecutionTool


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SYSTEM_PROMPT_TEMPLATE = """
# TASK
You are a data scientist that can resolve user's questions by calling `code_execution` tool to execute code.

# IMPORTANT: OUTPUT REQUIREMENTS
You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.

# Available data:
You have access to the following data when executing the code:
{registered_datasets_str}
"""

class ReactAgent(BaseAgent):
    
    name = "react_agent"

    def __init__(
        self, 
        model_name: str, 
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        self.agent_graph = self._create_agent_graph()


    def _build_system_prompt(self):
        registered_datasets_str = "\n".join([f"- {dataset}" for dataset in self.registered_datasets])
        return SYSTEM_PROMPT_TEMPLATE.format(registered_datasets_str=registered_datasets_str)

    def _get_tools(self):
        # return the tools for the agent
        tool_list = [CodeExecutionTool(sandbox=self.sandbox)]
        tool_dict = {tool.name: tool for tool in tool_list}
        return tool_dict
    
    def _agent_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to generate the response for the agent.
        """
        messages = state.messages
        system_prompt = self._build_system_prompt()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages

        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})

        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )

        # attach the tools with the model
        tool_dict = self._get_tools()
        tool_list = list(tool_dict.values())
        llm_with_tools = llm.bind_tools(tool_list)

        response = run_with_retry(llm_with_tools.invoke, arg=messages)

        return {
            "messages": [response],
        }


    def _tool_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to execute the tool for the agent.
        """
        tool_call = state.messages[-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        tool = self._get_tools()[tool_name]
        print(f"Executing tool: {tool_name} with input: {tool_input}")
        tool_output = tool._run(**tool_input)

        if tool_name == "code_execution":
            content = tool_output["stdout"]
            # update the code results
            code_result = CodeExecutionResult(
                code=tool_input["code"],
                console_output=tool_output["stdout"],
                running_time=tool_output["running_time"],
                peak_memory=tool_output["peak_memory_mb"],
            )
        else:
            content = tool_output
            code_result = None

        response = ToolMessage(
            content=content,
            name=tool_name,
            tool_call_id=tool_call["id"]
        )

        output_dict = {"messages": [response]}
        if code_result is not None:
            existing_code_results = state.code_execution_results
            existing_code_results.append(code_result)
            output_dict["code_execution_results"] = existing_code_results
        
        return output_dict

    def _should_continue(
        self,
        state: AgentState,
    ) -> Literal["tool_node", "end"]:
        """
        A function to determine whether to continue the agent loop or end.
        """
        last_message = state.messages[-1]

        # If no tool calls, we're done
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"

        # Otherwise continue to tools
        return "tool_node"

    def _create_agent_graph(self, debug: bool = False) -> StateGraph:    
        # the actual agent workflow graph
        workflow = StateGraph(
            AgentState,
            input=AgentState,
            output=AgentState
        )
        
        workflow.add_node("agent_node", self._agent_node)
        workflow.add_node("tool_node", self._tool_node)

        workflow.add_conditional_edges(
            "agent_node",
            self._should_continue,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        workflow.add_edge("tool_node", "agent_node")
        workflow.set_entry_point("agent_node")
        
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
                "messages": [("user", input_query)]
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