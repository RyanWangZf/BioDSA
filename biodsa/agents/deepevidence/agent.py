"""
Proposed by:

Wang, Z. et al. (2025). DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research. In submission.
"""

from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage, BaseMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.state import CodeExecutionResult
from biodsa.tools.code_exec_tool import CodeExecutionTool

from biodsa.agents.deepevidence.state import DeepEvidenceAgentState
from biodsa.agents.deepevidence.execution import DeepEvidenceExecutionResults
from biodsa.agents.deepevidence.prompt import (
    ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE,
    BFS_SYSTEM_PROMPT_TEMPLATE,
    DFS_SYSTEM_PROMPT_TEMPLATE
)

class DeepEvidenceAgent(BaseAgent):
    name = "deepevidence"
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
        # debug: visualize the agent graph
        # graph_object = self.agent_graph.get_graph(xray=1)
        # graph_object.draw_mermaid_png(output_file_path="deepevidence_graph.png", max_retries=5, retry_delay=2.0)
        # graph_object.print_ascii()

    def _create_agent_graph(self, debug: bool = False):
        """
        Create the agent graph for breadth-first search and depth-first search.
        """
        # breadth-first search sub-workflow
        bfs_workflow = StateGraph(
            DeepEvidenceAgentState,
            input=DeepEvidenceAgentState,
            output=DeepEvidenceAgentState
        )
        bfs_workflow.add_node("bfs_agent_node", self._bfs_agent_node)
        bfs_workflow.add_node("tool_node", self._tool_node)
        bfs_workflow.add_conditional_edges(
            "bfs_agent_node",
            self._should_continue_bfs_agent,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        bfs_workflow.add_edge("tool_node", "bfs_agent_node")
        bfs_workflow.set_entry_point("bfs_agent_node")
        bfs_workflow = bfs_workflow.compile(
            debug=debug,
            name="bfs_workflow"
        )

        # dfs sub-workflow
        dfs_workflow = StateGraph(
            DeepEvidenceAgentState,
            input=DeepEvidenceAgentState,
            output=DeepEvidenceAgentState
        )
        dfs_workflow.add_node("dfs_agent_node", self._dfs_agent_node)
        dfs_workflow.add_node("tool_node", self._tool_node)
        dfs_workflow.add_conditional_edges(
            "dfs_agent_node",
            self._should_continue_dfs_agent,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        dfs_workflow.add_edge("tool_node", "dfs_agent_node")
        dfs_workflow.set_entry_point("dfs_agent_node")
        dfs_workflow = dfs_workflow.compile(
            debug=debug,
            name="dfs_workflow"
        )

        # orchestrator
        # decide if we go bfs or dfs research on graph right now
        # decide which knowledge graph to do bfs and dfs research on
        orchestrator_workflow = StateGraph(
            DeepEvidenceAgentState,
            input=DeepEvidenceAgentState,
            output=DeepEvidenceAgentState
        )
        orchestrator_workflow.add_node("bfs_workflow", bfs_workflow)
        orchestrator_workflow.add_node("dfs_workflow", dfs_workflow)
        orchestrator_workflow.add_node("orchestrator_node", self._orchestrator_agent_node)
        orchestrator_workflow.add_node("tool_node", self._tool_node)
        orchestrator_workflow.add_conditional_edges(
            "orchestrator_node",
            self._should_go_which_sub_workflow,
            {
                "bfs_workflow": "bfs_workflow",
                "dfs_workflow": "dfs_workflow",
                "tool_node": "tool_node",
                "end": END
            }
        )
        orchestrator_workflow.add_edge("tool_node", "orchestrator_node")
        orchestrator_workflow.add_edge("bfs_workflow", "orchestrator_node")
        orchestrator_workflow.add_edge("dfs_workflow", "orchestrator_node")
        orchestrator_workflow.set_entry_point("orchestrator_node")
        orchestrator_workflow = orchestrator_workflow.compile(
            debug=debug,
            name="orchestrator_workflow"
        )
        return orchestrator_workflow

    def _build_system_prompt_for_orchestrator_agent(self):
        return ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE

    def _build_system_prompt_for_bfs_agent(self):
        return BFS_SYSTEM_PROMPT_TEMPLATE

    def _build_system_prompt_for_dfs_agent(self):
        return DFS_SYSTEM_PROMPT_TEMPLATE

    def _get_tools_for_orchestrator_agent(self):
        return []

    def _get_tools_for_bfs_agent(self):
        return []

    def _get_tools_for_dfs_agent(self):
        return []

    def _orchestrator_agent_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the orchestrator agent.
        """
        messages = state.messages
        system_prompt = self._build_system_prompt_for_orchestrator_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_orchestrator_agent()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {})
        )
        return {
            "messages": [response],
        }

    def _should_go_which_sub_workflow(self, state: DeepEvidenceAgentState) -> Literal["bfs_workflow", "dfs_workflow", "end"]:
        """
        A function to determine which sub-workflow to go to.
        """
        pass

    def _bfs_agent_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the breadth-first search agent.
        """
        messages = state.messages
        system_prompt = self._build_system_prompt_for_bfs_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_bfs_agent()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {})
        )
        return {
            "messages": [response],
        }

    def _dfs_agent_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the depth-first search agent.
        """
        messages = state.messages
        system_prompt = self._build_system_prompt_for_dfs_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_dfs_agent()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {})
        )
        return {
            "messages": [response],
        }

    def _tool_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the tool node.
        """
        pass

    def _should_continue_bfs_agent(self, state: DeepEvidenceAgentState) -> Literal["tool_node", "end"]:
        """
        A function to determine whether to continue the breadth-first search agent or end.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "tool_node"

    def _should_continue_dfs_agent(self, state: DeepEvidenceAgentState) -> Literal["tool_node", "end"]:
        """
        A function to determine whether to continue the depth-first search agent or end.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "tool_node"


    def generate(self, input_query: str, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        A function to generate the response for the agent.

        Args:
            input_query: The user query to process
            verbose: Whether to print the verbose output
        Returns:
            List[Dict[str, Any]]: The result from the agent graph or an error dict
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
    ) -> DeepEvidenceExecutionResults:
        """
        A function to execute the agent and return the execution results.

        Args:
            input_query: The user query to process
            verbose: Whether to print the verbose output
        Returns:
            DeepEvidenceExecutionResults: The execution results from the agent
        """
        results = self.generate(input_query, verbose=verbose)
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        code_execution_results = self._format_code_execution_results(final_state['code_execution_results'])
        final_response = final_state['messages'][-1].content

        return DeepEvidenceExecutionResults(
            sandbox=self.sandbox,
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response
        )
