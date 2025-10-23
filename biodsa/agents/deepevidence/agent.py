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

from biodsa.agents.deepevidence.state import (
    DeepEvidenceAgentState,
    BFSAgentState,
    DFSAgentState
)
from biodsa.agents.deepevidence.execution import DeepEvidenceExecutionResults
from biodsa.agents.deepevidence.prompt import (
    ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE,
    BFS_SYSTEM_PROMPT_TEMPLATE,
    DFS_SYSTEM_PROMPT_TEMPLATE
)
from biodsa.agents.deepevidence.orchestrator_tool import (
    create_bfs_tool,
    create_dfs_tool
)
from biodsa.agents.deepevidence.schema import KNOWLEDGE_BASE_TO_TOOLS_MAP, KNOWLEDGE_BASE_LIST
from biodsa.utils.render_utils import render_message_colored


class DeepEvidenceAgent(BaseAgent):
    name = "deepevidence"
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        small_model_name: str = None, # an optional smaller model to help complete the analysis plan and other tasks
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

    def _call_bfs_workflow(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to call the breadth-first search workflow.
        """
        print("called: bfs_workflow")
        parent_graph_message = state.messages[-1]
        subgraph_tool_call_id = parent_graph_message.tool_calls[0]["id"]

        # build the inputs
        search_target = state.search_targets
        search_target = "\n\n".join(search_target)
        knowledge_bases = state.knowledge_bases
        inputs = {
            "messages": [HumanMessage(content=search_target)],
            "knowledge_bases": knowledge_bases
        }

        # invoke the subgraph for breadth-first search
        bfs_outputs = self.bfs_workflow.invoke(
            inputs,
            config=config
        )

        # transform the outputs so it is aligned with the DeepEvidenceAgentState's format
        # in the format of ToolMessage
        all_messages = bfs_outputs['messages']
        final_response = all_messages[-1].content
        response = ToolMessage(
            content=final_response,
            name="go_breadth_first_search",
            tool_call_id=subgraph_tool_call_id
        )

        # get the input and output tokens
        bfs_input_tokens, bfs_output_tokens = bfs_outputs.get('total_input_tokens', 0), bfs_outputs.get('total_output_tokens', 0    )
        total_input_tokens = state.total_input_tokens + bfs_input_tokens
        total_output_tokens = state.total_output_tokens + bfs_output_tokens
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }


    def _call_dfs_workflow(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to call the depth-first search workflow.
        """
        print("called: dfs_workflow")
        parent_graph_message = state.messages[-1]
        subgraph_tool_call_id = parent_graph_message.tool_calls[0]["id"]

        # trigger the subgraph
        search_targets = "\n\n".join(state.search_targets)
        knowledge_base = state.knowledge_bases[0] # only one knowledge base for DFS
        # build the inputs
        inputs = {
            "messages": [HumanMessage(content=search_targets)],
            "knowledge_base": knowledge_base
        }
        # invoke the subgraph for depth-first search
        dfs_outputs = self.dfs_workflow.invoke(inputs, config=config)
        all_messages = dfs_outputs['messages']
        final_response = all_messages[-1].content

        # transform the final response so it is aligned with the DeepEvidenceAgentState's format
        # in the format of AIMessage
        response = ToolMessage(
            content=final_response,
            name="go_depth_first_search",
            tool_call_id=subgraph_tool_call_id
        )

        # get the input and output tokens
        dfs_input_tokens, dfs_output_tokens = dfs_outputs.get('total_input_tokens', 0), dfs_outputs.get('total_output_tokens', 0)
        total_input_tokens = state.total_input_tokens + dfs_input_tokens
        total_output_tokens = state.total_output_tokens + dfs_output_tokens
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

    def _create_agent_graph(self, debug: bool = False):
        """
        Create the agent graph for breadth-first search and depth-first search.
        """
        # breadth-first search sub-workflow
        bfs_workflow = StateGraph(
            BFSAgentState,
            input=BFSAgentState,
            output=BFSAgentState
        )
        bfs_workflow.add_node("bfs_agent_node", self._bfs_agent_node)
        bfs_workflow.add_node("bfs_agent_tool_node", self._tool_node_for_bfs_agent)
        bfs_workflow.add_conditional_edges(
            "bfs_agent_node",
            self._should_continue_bfs_agent,
            {
                "bfs_agent_tool_node": "bfs_agent_tool_node",
                "end": END
            }
        )
        bfs_workflow.add_edge("bfs_agent_tool_node", "bfs_agent_node")
        bfs_workflow.set_entry_point("bfs_agent_node")
        self.bfs_workflow = bfs_workflow.compile(
            debug=debug,
            name="bfs_workflow"
        )

        # dfs sub-workflow
        dfs_workflow = StateGraph(
            DFSAgentState,
            input=DFSAgentState,
            output=DFSAgentState
        )
        dfs_workflow.add_node("dfs_agent_node", self._dfs_agent_node)
        dfs_workflow.add_node("dfs_agent_tool_node", self._tool_node_for_dfs_agent)
        dfs_workflow.add_conditional_edges(
            "dfs_agent_node",
            self._should_continue_dfs_agent,
            {
                "dfs_agent_tool_node": "dfs_agent_tool_node",
                "end": END
            }
        )
        dfs_workflow.add_edge("dfs_agent_tool_node", "dfs_agent_node")
        dfs_workflow.set_entry_point("dfs_agent_node")
        self.dfs_workflow = dfs_workflow.compile(
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
        orchestrator_workflow.add_node("bfs_workflow", self._call_bfs_workflow)
        orchestrator_workflow.add_node("dfs_workflow", self._call_dfs_workflow)
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

    def _get_tools_for_orchestrator_agent(self, allowed_knowledge_bases: List[str] = None):
        """
        Get tools for the orchestrator agent with dynamically constrained knowledge bases.

        Args:
            allowed_knowledge_bases: List of knowledge bases to make available.
                                    If None, all knowledge bases are available.
        """
        if allowed_knowledge_bases is None:
            allowed_knowledge_bases = KNOWLEDGE_BASE_LIST

        # Create tools dynamically based on allowed knowledge bases
        bfs_tool_class = create_bfs_tool(allowed_knowledge_bases)
        dfs_tool_class = create_dfs_tool(allowed_knowledge_bases)

        return [bfs_tool_class(), dfs_tool_class(), CodeExecutionTool()]

    def _get_tools_for_bfs_agent(self, knowledge_bases: List[str]):
        kg_tools = []
        for knowledge_base in knowledge_bases:
            kg_tools.extend(KNOWLEDGE_BASE_TO_TOOLS_MAP[knowledge_base])
        return kg_tools + [CodeExecutionTool()]

    def _get_tools_for_dfs_agent(self, knowledge_base: str):
        kg_tools = KNOWLEDGE_BASE_TO_TOOLS_MAP[knowledge_base]
        return kg_tools + [CodeExecutionTool()]

    def _orchestrator_agent_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the orchestrator agent.
        """
        # build the system prompt and call the model
        messages = state.messages
        system_prompt = self._build_system_prompt_for_orchestrator_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages

        # Get allowed knowledge bases from state (user-specified)
        allowed_knowledge_bases = state.knowledge_bases if state.knowledge_bases else KNOWLEDGE_BASE_LIST
        tools = self._get_tools_for_orchestrator_agent(allowed_knowledge_bases)

        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {}),
            parallel_tool_calls=False,
        )

        # parse the response to get if any bfs or dfs workflow should be started
        knowledge_bases: List[str] = []
        search_targets: List[str] = []
        if response.tool_calls is not None:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "go_breadth_first_search":
                    knowledge_bases.extend(tool_call["args"]["knowledge_bases"])
                    search_targets.append(tool_call["args"]["search_target"])
                elif tool_call["name"] == "go_depth_first_search":
                    knowledge_bases.append(tool_call["args"]["knowledge_base"])
                    search_targets.append(tool_call["args"]["search_target"])
                else:
                    pass
            knowledge_bases = list(set(knowledge_bases))
            search_targets = list(set(search_targets))

        # get the input and output tokens
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens

        # update the state
        return {
            "messages": [response],
            "knowledge_bases": knowledge_bases,
            "search_targets": search_targets,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

    def _should_go_which_sub_workflow(self, state: DeepEvidenceAgentState) -> Literal["bfs_workflow", "dfs_workflow", "end"]:
        """
        A function to determine which sub-workflow to go to.
        """
        last_message = state.messages[-1]
        tool_calls = last_message.tool_calls
        if tool_calls is not None:
            for tool_call in tool_calls:
                if tool_call["name"] == "go_breadth_first_search":
                    return "bfs_workflow"
                elif tool_call["name"] == "go_depth_first_search":
                    return "dfs_workflow"
                else:
                    return "tool_node"
        return "end"

    def _bfs_agent_node(self, state: BFSAgentState, config: RunnableConfig) -> BFSAgentState:
        """
        A function to execute the breadth-first search agent.
        """
        messages = state.messages
        knowledge_bases = state.knowledge_bases
        system_prompt = self._build_system_prompt_for_bfs_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_bfs_agent(knowledge_bases=knowledge_bases)
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {})
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

    def _dfs_agent_node(self, state: DFSAgentState, config: RunnableConfig) -> DFSAgentState:
        """
        A function to execute the depth-first search agent.
        """
        messages = state.messages
        knowledge_base = state.knowledge_base
        system_prompt = self._build_system_prompt_for_dfs_agent()
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages
        tools = self._get_tools_for_dfs_agent(knowledge_base=knowledge_base)
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=config.get("configurable", {}).get("model_kwargs", {})
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

    def _tool_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the tool node for the orchestrator agent.
        """
        messages = state.messages
        allowed_knowledge_bases = state.knowledge_bases if state.knowledge_bases else KNOWLEDGE_BASE_LIST
        tool_call = messages[-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        available_tools = self._get_tools_for_orchestrator_agent(allowed_knowledge_bases=allowed_knowledge_bases)
        available_tools_dict = {tool.name: tool for tool in available_tools}
        called_tool = available_tools_dict[tool_name]
        tool_output = called_tool._run(**tool_input)
        response = ToolMessage(
            content=tool_output,
            name=tool_name,
            tool_call_id=tool_call["id"]
        )
        return {
            "messages": [response],
        }

    def _tool_node_for_bfs_agent(self, state: BFSAgentState, config: RunnableConfig) -> BFSAgentState:
        """
        A function to execute the tool node for the breadth-first search agent.
        """
        knowledge_bases = state.knowledge_bases
        tool_call = state.messages[-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        available_tools = self._get_tools_for_bfs_agent(knowledge_bases=knowledge_bases)
        available_tools_dict = {tool.name: tool for tool in available_tools}
        called_tool = available_tools_dict[tool_name]
        tool_output = called_tool._run(**tool_input)
        response = ToolMessage(
            content=tool_output,
            name=tool_name,
            tool_call_id=tool_call["id"]
        )
        return {
            "messages": [response],
        }

    def _tool_node_for_dfs_agent(self, state: DFSAgentState, config: RunnableConfig) -> DFSAgentState:
        """
        A function to execute the tool node for the depth-first search agent.
        """
        knowledge_base = state.knowledge_base
        tool_call = state.messages[-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        available_tools = self._get_tools_for_dfs_agent(knowledge_base=knowledge_base)
        available_tools_dict = {tool.name: tool for tool in available_tools}
        called_tool = available_tools_dict[tool_name]
        tool_output = called_tool._run(**tool_input)
        response = ToolMessage(
            content=tool_output,
            name=tool_name,
            tool_call_id=tool_call["id"]
        )
        return {
            "messages": [response],
        }

    def _should_continue_bfs_agent(self, state: BFSAgentState) -> Literal["bfs_agent_tool_node", "end"]:
        """
        A function to determine whether to continue the breadth-first search agent or end.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "bfs_agent_tool_node"

    def _should_continue_dfs_agent(self, state: DFSAgentState) -> Literal["dfs_agent_tool_node", "end"]:
        """
        A function to determine whether to continue the depth-first search agent or end.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        return "dfs_agent_tool_node"


    def generate(self, input_query: str, knowledge_bases: List[str] = None, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        A function to generate the response for the agent.

        Args:
            input_query: The user query to process
            knowledge_bases: List of knowledge bases available to the agent. If None, uses all available.
            verbose: Whether to print the verbose output
        Returns:
            List[Dict[str, Any]]: The result from the agent graph or an error dict
        """
        assert self.agent_graph is not None, "Agent graph is not set"

        # Extract input_query from kwargs
        if input_query is None:
            return [{"error": "input_query is required"}]

        # Set default if not provided
        if knowledge_bases is None:
            knowledge_bases = KNOWLEDGE_BASE_LIST

        try:
            all_results = []
            inputs = {
                "messages": [("user", input_query)],
                "user_query": input_query,
                "knowledge_bases": knowledge_bases
            }

            # Invoke the agent graph and return the result
            for streamed_chunk in self.agent_graph.stream(
                inputs,
                stream_mode = ["values"],
                subgraphs=True,
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
                chunk = streamed_chunk[-1]
                if verbose:
                    last_message = chunk['messages'][-1]
                    # Use colored rendering for better visualization
                    print(render_message_colored(last_message, show_tool_calls=True))
                all_results.append(chunk)
            return all_results

        except Exception as e:
            print(f"Error streaming response: {e}")
            raise e

    def go(
        self,
        input_query: str,
        knowledge_bases: List[str] = None,
        verbose: bool = True,
    ) -> DeepEvidenceExecutionResults:
        """
        A function to execute the agent and return the execution results.

        Args:
            input_query: The user query to process
            knowledge_bases: List of knowledge bases to make available for the agent.
                           If None, all predefined knowledge bases are available.
                           Must be a subset of: {KNOWLEDGE_BASE_LIST}
            verbose: Whether to print the verbose output
        Returns:
            DeepEvidenceExecutionResults: The execution results from the agent
        """
        # Validate and set default knowledge bases
        if knowledge_bases is None:
            knowledge_bases = KNOWLEDGE_BASE_LIST
        else:
            # Validate that all specified knowledge bases are in the predefined list
            for kb in knowledge_bases:
                if kb not in KNOWLEDGE_BASE_LIST:
                    raise ValueError(f"Unknown knowledge base: {kb}. Must be one of {KNOWLEDGE_BASE_LIST}")

        results = self.generate(input_query, knowledge_bases=knowledge_bases, verbose=verbose)
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        code_execution_results = self._format_code_execution_results(final_state.get('code_execution_results', []))
        total_input_tokens = final_state['total_input_tokens']
        total_output_tokens = final_state['total_output_tokens']
        final_response = final_state['messages'][-1].content

        return DeepEvidenceExecutionResults(
            sandbox=self.sandbox,
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens
        )