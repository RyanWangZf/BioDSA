import re
import logging
from typing import Dict, Any, List, Literal, Union
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry, cut_off_tokens
from biodsa.agents.state import AgentState, CodeExecutionResult
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SYSTEM_PROMPT = """
# TASK
Given the user's ask, you should use the code execution tool to execute code to answer the user's question.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.

You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
- print(statistical_test_output)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.
"""

FINAL_ANSWER_PROMPT = """
# TASK
Evaluate the user's ask taking into account the evidence provided.

# IMPORTANT
You should make your final answer completely based on the observations provided.
Do not make any assumptions or include any other information which is not included in the observations.

# FINAL ANSWER
The final answer is one of the following values:

True - the hypothesis is supported by the data
False - the hypothesis is not supported by the data
Not Verifiable - The hypothesis is not verifiable with the provided datasets

As a part of the final answer, you must output
- analysis: a list of concise analyses that justifies your evaluation of the hypothesis
- final_answer: one of the following values: True, False, Not Verifiable
"""

# create a code execution tool
class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = "Execute code to answer the user's question"
    sandbox: ExecutionSandboxWrapper = None

    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(self, code: str) -> str:
        # execute the code
        exit_code, output, artifacts, running_time, peak_memory_mb = self.sandbox.execute(
            language="python",
            code=code
        )
        stdout = cut_off_tokens(output, 4096)
        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "artifacts": artifacts,
            "running_time": running_time,
            "peak_memory_mb": peak_memory_mb,
        }

class ReactAgent(BaseAgent):
    
    name = "react_agent"

    def __init__(
        self, 
        model_name: str, 
        api_type: str,
        api_key: str,
        endpoint: str,
        sandbox: ExecutionSandboxWrapper = None
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
        )
        
        # if it is not None, the sandbox will be used for executing the code
        # otherwise, it will only generate the code
        self.sandbox = sandbox

        self.agent_graph = self.create_agent_graph()

    def get_tools(self):
        # return the tools for the agent
        tool_list = [CodeExecutionTool(sandbox=self.sandbox)]
        tool_dict = {tool.name: tool for tool in tool_list}
        return tool_dict
    
    def agent_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to generate the response for the agent.
        """
        messages = state.messages        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
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


    def tool_node(
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
            existing_code_results = state.code_results
            existing_code_results.append(code_result)
            output_dict["code_results"] = existing_code_results
        
        return output_dict

    def should_continue(
        self,
        state: AgentState,
    ) -> Union[str, list]:
        """
        A function to determine whether to continue the agent loop or end.
        """
        last_message = state.messages[-1]

        # If no tool calls, we're done
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "final_response"

        # Otherwise continue to tools
        return "tool_node"

    # def final_response(
    #     self,
    #     state: AgentState,
    #     config: RunnableConfig,
    # ) -> AgentState:

    #     # use the final response model to generate the final response
    #     llm = self._get_model(
    #         api=self.api_type,
    #         model_name=self.model_name,
    #         api_key=self.api_key,
    #         endpoint=self.endpoint,
    #         max_completion_tokens=5000,
    #     )
        
    #     model_with_structured_output = llm.with_structured_output(FinalResponseForStructuring)
        
    #     messages = state.messages
        
    #     messages = [
    #         SystemMessage(content=FINAL_ANSWER_PROMPT),
    #     ] + messages
        
    #     response = run_with_retry(model_with_structured_output.invoke, arg=messages)
        
    #     return FinalResponse(
    #         executions=state.code_results,
    #         final_answer=response.final_answer,
    #         analysis=response.analysis
    #     )

    def create_agent_graph(self, debug: bool = False) -> StateGraph:    
        # the actual agent workflow graph
        workflow = StateGraph(
            AgentState,
            input=AgentState,
            output=AgentState
        )
        
        workflow.add_node("agent_node", self.agent_node)
        workflow.add_node("final_response", self.final_response)
        workflow.add_node("tool_node", self.tool_node)

        workflow.add_conditional_edges(
            "agent_node",
            self.should_continue,
            {
                "tool_node": "tool_node",
                "final_response": "final_response"
            }
        )
        workflow.add_edge("tool_node", "agent_node")
        workflow.add_edge("final_response", END)
        workflow.set_entry_point("agent_node")
        
        workflow = workflow.compile(
            debug=debug,
            name=self.name
        )
        return workflow
    
    def generate(
        self,
        input_query: str
    ) -> Dict[str, Any]:
        """
        Override the base method for generating code.
        
        Args:
            input_query: The user query to process
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Extract input_query from kwargs
        if input_query is None:
            return {"error": "input_query is required"}
        
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
                all_results.append(chunk)
            return all_results
            
        except Exception as e:
            print(f"Error streaming code: {e}")
            raise e
    