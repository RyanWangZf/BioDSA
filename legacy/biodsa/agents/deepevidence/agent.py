"""
Proposed by:

Wang, Z. et al. (2025). DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research. In submission.
"""
import shutil
import os
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent
from biodsa.tool_wrappers.code_exec_tool import CodeExecutionTool

from biodsa.agents.deepevidence.state import (
    DeepEvidenceAgentState,
    BFSAgentState,
    DFSAgentState
)
from biodsa.agents.deepevidence.execution import DeepEvidenceExecutionResults
from biodsa.agents.deepevidence.prompt import (
    ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE,
    BFS_SYSTEM_PROMPT_TEMPLATE,
    DFS_SYSTEM_PROMPT_TEMPLATE,
    MEMORY_GRAPH_PROTOCOL_PROMPT,
    SEARCH_ROUNDS_BUDGET_PROMPT,
    ACTION_ROUNDS_BUDGET_PROMPT
)
from biodsa.agents.deepevidence.prompt import (
    PUBMED_PAPERS_KB_PROMPT,
    GENE_SET_KB_PROMPT,
    DISEASE_KB_PROMPT,
    DRUG_KB_PROMPT,
    VARIANT_KB_PROMPT,
)
from biodsa.agents.deepevidence.orchestrator_tool import (
    create_bfs_tool,
    create_dfs_tool
)
from biodsa.agents.deepevidence.schema import KNOWLEDGE_BASE_TO_TOOLS_MAP, KNOWLEDGE_BASE_LIST
from biodsa.utils.render_utils import render_message_colored
from biodsa.memory.graph import AddToGraph, RetrieveFromGraph, load_graph_data
from biodsa.memory.memory_graph import get_default_memory_graph_cache_dir, clear_manager_cache
from biodsa.tool_wrappers.pubmed.tools import (
    FindEntitiesTool,
    FindRelatedEntitiesTool,
)
from biodsa.tool_wrappers.umls.tools import (
    SearchUMLSEntitiesTool
)
from biodsa.agents.deepevidence.tool_wrappers.genes.tools import (
    UnifiedGeneSearchTool,
    UnifiedGeneDetailsFetchTool,
)
from biodsa.agents.deepevidence.tool_wrappers.diseases.tools import (
    UnifiedDiseaseSearchTool,
    UnifiedDiseaseDetailsFetchTool,
)
from biodsa.agents.deepevidence.tool_wrappers.drugs.tools import (
    UnifiedDrugSearchTool,
    UnifiedDrugDetailsFetchTool,
)

class DeepEvidenceAgent(BaseAgent):
    name = "deepevidence"
    small_model_name: str = None
    small_model_kwargs: Dict[str, Any] = None
    small_model_api_type: str = None
    small_model_api_key: str = None
    small_model_endpoint: str = None
    evidence_graph_name: str = "evidence_graph"
    evidence_graph_cache_dir: str = None
    main_search_rounds_budget: int = 5
    main_action_rounds_budget: int = 20
    subagent_action_rounds_budget: int = 5

    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str=None,
        container_id: str = None,
        model_kwargs: Dict[str, Any] = None,
        small_model_name: str = None,
        small_model_kwargs: Dict[str, Any] = None,
        small_model_api_type: str = None,
        small_model_api_key: str = None,
        small_model_endpoint: str = None,
        evidence_graph_cache_dir: str = None,
        main_search_rounds_budget: int = 5,
        main_action_rounds_budget: int = 20,
        subagent_action_rounds_budget: int = 5,
        light_mode: bool = False,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
            model_kwargs=model_kwargs,
            llm_timeout=llm_timeout,
        )
        if small_model_name is None:
            self.small_model_name = self.model_name
            self.small_model_kwargs = self.model_kwargs
            self.small_model_api_type = self.api_type
            self.small_model_api_key = self.api_key
            self.small_model_endpoint = self.endpoint
        else:
            self.small_model_name = small_model_name
            self.small_model_kwargs = small_model_kwargs
            self.small_model_api_type = small_model_api_type
            self.small_model_api_key = small_model_api_key
            self.small_model_endpoint = small_model_endpoint

        if evidence_graph_cache_dir is None:
            # assign a default value
            evidence_graph_cache_dir = get_default_memory_graph_cache_dir()

        self.evidence_graph_cache_dir = evidence_graph_cache_dir
        self.main_search_rounds_budget = main_search_rounds_budget
        self.main_action_rounds_budget = main_action_rounds_budget
        self.subagent_action_rounds_budget = subagent_action_rounds_budget
        self.main_search_rounds_budget = main_search_rounds_budget
        self.umls_api_key = os.getenv("UMLS_API_KEY")

        self.light_mode = light_mode # a light mode agent that does not use the memory graph
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
        parent_graph_message_tool_calls = parent_graph_message.tool_calls
        # find the one with name "go_breadth_first_search"
        for tool_call in parent_graph_message_tool_calls:
            if tool_call["name"] == "go_breadth_first_search":
                subgraph_tool_call_id = tool_call["id"]
                break
        else:
            raise ValueError("No go_breadth_first_search tool call found in the parent graph message or the tool call does not have the required arguments")

        # build the inputs
        search_target = state.search_targets
        search_target = "\n\n".join(search_target)
        knowledge_bases = state.subagent_knowledge_bases
        action_rounds_budget = state.search_rounds_budget
        action_rounds_budget = min(action_rounds_budget, self.subagent_action_rounds_budget)
        action_rounds_budget = max(action_rounds_budget, 3) # minimum 3 rounds of action is required

        # prepare the inputs
        inputs = {
            "messages": [HumanMessage(content=search_target)],
            "knowledge_bases": knowledge_bases,
            "action_rounds_budget": action_rounds_budget,
            "current_round": 0,
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
        parent_graph_message_tool_calls = parent_graph_message.tool_calls
        # find the one with name "go_depth_first_search"
        for tool_call in parent_graph_message_tool_calls:
            if tool_call["name"] == "go_depth_first_search":
                subgraph_tool_call_id = tool_call["id"]
                break
        else:
            raise ValueError("No go_depth_first_search tool call found in the parent graph message or the tool call does not have the required arguments")

        # trigger the subgraph
        search_targets = "\n\n".join(state.search_targets)
        knowledge_bases = state.subagent_knowledge_bases
        action_rounds_budget = state.search_rounds_budget
        action_rounds_budget = min(action_rounds_budget, self.subagent_action_rounds_budget)
        action_rounds_budget = max(action_rounds_budget, 3) # minimum 3 rounds of action is required

        # prepare the inputs
        inputs = {
            "messages": [HumanMessage(content=search_targets)],
            "knowledge_bases": knowledge_bases, # multiple knowledge bases for DFS
            "action_rounds_budget": action_rounds_budget,
            "current_round": 0,
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

    def _build_system_prompt_for_orchestrator_agent(self, knowledge_bases: List[str]=None):
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE.format(workdir=self.workdir)
        if not self.light_mode:
            system_prompt += MEMORY_GRAPH_PROTOCOL_PROMPT
        if "gene" in knowledge_bases:
            system_prompt += GENE_SET_KB_PROMPT
        if "disease" in knowledge_bases:
            system_prompt += DISEASE_KB_PROMPT
        if "drug" in knowledge_bases:
            system_prompt += DRUG_KB_PROMPT
        if "variant" in knowledge_bases:
            system_prompt += VARIANT_KB_PROMPT
        if "pubmed_papers" in knowledge_bases:
            system_prompt += PUBMED_PAPERS_KB_PROMPT
        return system_prompt

    def _build_system_prompt_for_bfs_agent(self, knowledge_bases: List[str]=None):
        system_prompt = BFS_SYSTEM_PROMPT_TEMPLATE.format(workdir=self.workdir)
        if "gene" in knowledge_bases:
            system_prompt += GENE_SET_KB_PROMPT
        if "disease" in knowledge_bases:
            system_prompt += DISEASE_KB_PROMPT
        if "drug" in knowledge_bases:
            system_prompt += DRUG_KB_PROMPT
        if "variant" in knowledge_bases:
            system_prompt += VARIANT_KB_PROMPT
        if "pubmed_papers" in knowledge_bases:
            system_prompt += PUBMED_PAPERS_KB_PROMPT
        return system_prompt

    def _build_system_prompt_for_dfs_agent(self, knowledge_bases: List[str]=None):
        system_prompt = DFS_SYSTEM_PROMPT_TEMPLATE.format(workdir=self.workdir)
        if "gene" in knowledge_bases:
            system_prompt += GENE_SET_KB_PROMPT
        if "disease" in knowledge_bases:
            system_prompt += DISEASE_KB_PROMPT
        if "drug" in knowledge_bases:
            system_prompt += DRUG_KB_PROMPT
        if "variant" in knowledge_bases:
            system_prompt += VARIANT_KB_PROMPT
        if "pubmed_papers" in knowledge_bases:
            system_prompt += PUBMED_PAPERS_KB_PROMPT
        return system_prompt

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
        bfs_tool_class = create_bfs_tool(allowed_knowledge_bases= allowed_knowledge_bases, maximum_search_rounds=self.subagent_action_rounds_budget)
        tools = [bfs_tool_class(), CodeExecutionTool(self.sandbox)]

        dfs_tool_class = create_dfs_tool(allowed_knowledge_bases= allowed_knowledge_bases, maximum_search_rounds=self.subagent_action_rounds_budget)
        tools.append(dfs_tool_class())

        if not self.light_mode:
            # add retrieve graph tool
            tools.append(RetrieveFromGraph(
                database_name=self.evidence_graph_name,
                cache_dir=self.evidence_graph_cache_dir
            ))
            tools.append(AddToGraph(
                database_name=self.evidence_graph_name,
                cache_dir=self.evidence_graph_cache_dir
            ))

        if "pubmed_papers" in allowed_knowledge_bases:
            # add entity recognition tool
            tools.extend([
                FindEntitiesTool(sandbox=self.sandbox),
                FindRelatedEntitiesTool(sandbox=self.sandbox)
            ])

        if "gene" in allowed_knowledge_bases:
            tools.append(UnifiedGeneSearchTool(sandbox=self.sandbox))

        if "disease" in allowed_knowledge_bases:
            tools.append(UnifiedDiseaseSearchTool(sandbox=self.sandbox))
            
        if "drug" in allowed_knowledge_bases:
            tools.append(UnifiedDrugSearchTool(sandbox=self.sandbox))

        if self.umls_api_key is not None:
            tools.append(SearchUMLSEntitiesTool(umls_api_key=self.umls_api_key, sandbox=self.sandbox))

        return tools

    def _get_tools_for_bfs_agent(self, knowledge_bases: List[str]):
        kg_tools = []
        for knowledge_base in knowledge_bases:
            for tool_class in KNOWLEDGE_BASE_TO_TOOLS_MAP[knowledge_base]:
                initialized_tool = tool_class(sandbox=self.sandbox)
                kg_tools.append(initialized_tool)
        tools = kg_tools + [CodeExecutionTool(self.sandbox)]
        return tools

    def _get_tools_for_dfs_agent(self, knowledge_bases: List[str]):
        kg_tools = []
        for knowledge_base in knowledge_bases:
            for tool_class in KNOWLEDGE_BASE_TO_TOOLS_MAP[knowledge_base]:
                initialized_tool = tool_class(sandbox=self.sandbox)
                kg_tools.append(initialized_tool)
        tools = kg_tools + [CodeExecutionTool(self.sandbox)]
        return tools

    def _orchestrator_agent_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the orchestrator agent.
        """
        # Get allowed knowledge bases from state (user-specified)
        allowed_knowledge_bases = state.knowledge_bases if state.knowledge_bases else KNOWLEDGE_BASE_LIST
        tools = self._get_tools_for_orchestrator_agent(allowed_knowledge_bases)

        # build the system prompt and call the model
        messages = state.messages
        system_prompt = self._build_system_prompt_for_orchestrator_agent(knowledge_bases=allowed_knowledge_bases)
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages

        # Track both round counters
        current_round = state.current_round  # Number of BFS/DFS search rounds
        current_action_round = state.current_action_round  # Total orchestrator calls
        
        # build the search rounds budget prompt
        search_rounds_budget_prompt = SEARCH_ROUNDS_BUDGET_PROMPT.format(current_round=current_round, search_rounds_budget=self.main_search_rounds_budget)
        messages.append(HumanMessage(content=search_rounds_budget_prompt))
        
        # build the action rounds budget prompt
        action_rounds_budget_prompt = ACTION_ROUNDS_BUDGET_PROMPT.format(current_round=current_action_round, action_rounds_budget=self.main_action_rounds_budget)
        messages.append(HumanMessage(content=action_rounds_budget_prompt))

        # call the model
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs,
            parallel_tool_calls=False,
        )

        # parse the response to get if any bfs or dfs workflow should be started
        subagent_knowledge_bases: List[str] = []
        search_targets: List[str] = []
        if response.tool_calls is not None:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "go_breadth_first_search":
                    subagent_knowledge_bases.extend(tool_call["args"]["knowledge_bases"])
                    search_targets.append(tool_call["args"]["search_target"])
                    current_round += 1 # only add 1 to the current round for bfs
                elif tool_call["name"] == "go_depth_first_search":
                    subagent_knowledge_bases.extend(tool_call["args"]["knowledge_bases"])
                    search_targets.append(tool_call["args"]["search_target"])
                    current_round += 1 # only add 1 to the current round for dfs
                else:
                    # otherwise, no need to add search round because the agent might do some other tasks right now
                    pass
            subagent_knowledge_bases = list(set(subagent_knowledge_bases))
            search_targets = list(set(search_targets))

        # Increment action round counter (this happens every time orchestrator is called)
        current_action_round += 1

        # get the input and output tokens
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens

        print(f"Current search round (BFS/DFS calls): {current_round}/{self.main_search_rounds_budget}")
        print(f"Current action round (orchestrator calls): {current_action_round}/{self.main_action_rounds_budget}")

        # update the state
        return {
            "messages": [response],
            "subagent_knowledge_bases": subagent_knowledge_bases,
            "search_targets": search_targets,
            "current_round": current_round,
            "current_action_round": current_action_round,
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
        current_round = state.current_round
        system_prompt = self._build_system_prompt_for_bfs_agent(
            knowledge_bases=knowledge_bases,
        )
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages

        # build the action rounds budget prompt
        action_rounds_budget = state.action_rounds_budget
        action_round_budget_prompt = ACTION_ROUNDS_BUDGET_PROMPT.format(current_round=current_round, action_rounds_budget=action_rounds_budget)
        messages.append(HumanMessage(content=action_round_budget_prompt))

        tools = self._get_tools_for_bfs_agent(knowledge_bases=knowledge_bases)
        response = self._call_model(
            model_name=self.small_model_name,
            api_type=self.small_model_api_type,
            api_key=self.small_model_api_key,
            endpoint=self.small_model_endpoint,
            messages=messages,
            tools=tools,
            model_kwargs=self.small_model_kwargs,
            parallel_tool_calls=False,
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens
        current_round += 1

        # update the state
        print(f"Current round of the breadth-first search agent: {current_round}/{action_rounds_budget}")
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "current_round": current_round,
        }

    def _dfs_agent_node(self, state: DFSAgentState, config: RunnableConfig) -> DFSAgentState:
        """
        A function to execute the depth-first search agent.
        """
        messages = state.messages
        knowledge_bases = state.knowledge_bases
        system_prompt = self._build_system_prompt_for_dfs_agent(knowledge_bases=knowledge_bases)
        messages = [
            SystemMessage(content=system_prompt),
        ] + messages

        # build the action rounds budget prompt
        current_round = state.current_round
        action_rounds_budget = state.action_rounds_budget
        action_round_budget_prompt = ACTION_ROUNDS_BUDGET_PROMPT.format(current_round=current_round, action_rounds_budget=action_rounds_budget)
        messages.append(HumanMessage(content=action_round_budget_prompt))

        tools = self._get_tools_for_dfs_agent(knowledge_bases=knowledge_bases)
        response = self._call_model(
            model_name=self.small_model_name,
            api_type=self.small_model_api_type,
            api_key=self.small_model_api_key,
            endpoint=self.small_model_endpoint,
            messages=messages,
            tools=tools,
            model_kwargs=self.small_model_kwargs,
            parallel_tool_calls=False,
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        total_input_tokens = state.total_input_tokens + input_tokens
        total_output_tokens = state.total_output_tokens + output_tokens
        current_round += 1
        print(f"Current round of the depth-first search agent: {current_round}/{action_rounds_budget}")
        return {
            "messages": [response],
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "current_round": current_round,
        }

    def _tool_node(self, state: DeepEvidenceAgentState, config: RunnableConfig) -> DeepEvidenceAgentState:
        """
        A function to execute the tool node for the orchestrator agent.
        """
        messages = state.messages
        allowed_knowledge_bases = state.knowledge_bases if state.knowledge_bases else KNOWLEDGE_BASE_LIST
        all_tool_calls = messages[-1].tool_calls
        responses = []
        for tool_call in all_tool_calls:
            tool_call_id = tool_call["id"]
            try:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]

                available_tools = self._get_tools_for_orchestrator_agent(allowed_knowledge_bases=allowed_knowledge_bases)
                available_tools_dict = {tool.name: tool for tool in available_tools}
                called_tool = available_tools_dict[tool_name]
                tool_output = called_tool._run(**tool_input)
                response = ToolMessage(
                        content=tool_output,
                        name=tool_name,
                        tool_call_id=tool_call_id
                    )
            except Exception as e:
                print(f"Error executing tool {tool_name} with input {tool_input}: {e}")
                response = ToolMessage(
                    content=f"Error executing tool {tool_name} with input {tool_input}: {e}",
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            responses.append(response)
        return {
            "messages": responses,
        }

    def _tool_node_for_bfs_agent(self, state: BFSAgentState, config: RunnableConfig) -> BFSAgentState:
        """
        A function to execute the tool node for the breadth-first search agent.
        """
        knowledge_bases = state.knowledge_bases
        all_tool_calls = state.messages[-1].tool_calls
        responses = []
        for tool_call in all_tool_calls:
            tool_call_id = tool_call["id"]
            try:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]
                available_tools = self._get_tools_for_bfs_agent(knowledge_bases=knowledge_bases)
                available_tools_dict = {tool.name: tool for tool in available_tools}
                called_tool = available_tools_dict[tool_name]
                tool_output = called_tool._run(**tool_input)
                response = ToolMessage(
                    content=tool_output,
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            except Exception as e:
                print(f"Error executing tool {tool_name} with input {tool_input}: {e}")
                response = ToolMessage(
                    content=f"Error executing tool {tool_name} with input {tool_input}: {e}",
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            responses.append(response)
        return {
            "messages": responses,
        }

    def _tool_node_for_dfs_agent(self, state: DFSAgentState, config: RunnableConfig) -> DFSAgentState:
        """
        A function to execute the tool node for the depth-first search agent.
        """
        knowledge_bases = state.knowledge_bases
        all_tool_calls = state.messages[-1].tool_calls
        responses = []
        for tool_call in all_tool_calls:
            tool_call_id = tool_call["id"]
            try:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]
                available_tools = self._get_tools_for_dfs_agent(knowledge_bases=knowledge_bases)
                available_tools_dict = {tool.name: tool for tool in available_tools}
                called_tool = available_tools_dict[tool_name]
                tool_output = called_tool._run(**tool_input)
                response = ToolMessage(
                    content=tool_output,
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            except Exception as e:
                print(f"Error executing tool {tool_name} with input {tool_input}: {e}")
                response = ToolMessage(
                    content=f"Error executing tool {tool_name} with input {tool_input}: {e}",
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            responses.append(response)
        return {
            "messages": responses,
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
                    "recursion_limit": 100
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
        clear_evidence_graph_cache: bool = True,
    ) -> DeepEvidenceExecutionResults:
        """
        A function to execute the agent and return the execution results.

        Args:
            input_query: The user query to process
            knowledge_bases: List of knowledge bases to make available for the agent.
                           If None, all predefined knowledge bases are available.
                           Must be a subset of: {KNOWLEDGE_BASE_LIST}
            verbose: Whether to print the verbose output
            clear_evidence_graph_cache: Whether to clear the evidence graph cache before running the agent
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

        if clear_evidence_graph_cache:
            # remove everything under the evidence_graph_cache_dir
            if self.evidence_graph_cache_dir is not None:
                if os.path.exists(self.evidence_graph_cache_dir):
                    shutil.rmtree(self.evidence_graph_cache_dir)
                    os.makedirs(self.evidence_graph_cache_dir, exist_ok=True)
                # Clear the cached KnowledgeGraphManager instance to avoid reusing stale data
                clear_manager_cache(cache_dir=self.evidence_graph_cache_dir)
            else:
                raise ValueError("evidence_graph_cache_dir is not set")

        results = self.generate(input_query, knowledge_bases=knowledge_bases, verbose=verbose)
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        code_execution_results = self._format_code_execution_results(final_state.get('code_execution_results', []))
        total_input_tokens = final_state['total_input_tokens']
        total_output_tokens = final_state['total_output_tokens']
        final_response = final_state['messages'][-1].content

        # fetch the full evidence graph data
        if not self.light_mode:
            evidence_graph_data = load_graph_data(context=self.evidence_graph_name, cache_dir=self.evidence_graph_cache_dir)
        else:
            evidence_graph_data = {}

        return DeepEvidenceExecutionResults(
            sandbox=self.sandbox,
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            evidence_graph_data=evidence_graph_data,
        )