from pydantic import BaseModel
from typing import List, Annotated, Sequence, Dict, Any
from langgraph.graph.message import add_messages, BaseMessage

from biodsa.agents.state import CodeExecutionResult

class DeepEvidenceAgentState(BaseModel):
    """State for the deep evidence agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    analysis_plan: str = ""
    user_query: str = ""
    knowledge_bases: List[str] = []  # List of available knowledge bases (user-specified)
    search_targets: List[str] = []
    search_rounds_budget: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    subgraph_tool_call_ids: List[str] = []
    current_round: int = 0  # Number of BFS/DFS search rounds called
    current_action_round: int = 0  # Total number of orchestrator agent calls
    subagent_knowledge_bases: List[str] = [] # passed to the sub-agents

class BFSAgentState(BaseModel):
    """State for the breadth-first search agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    search_target: str = ""
    knowledge_bases: List[str] = []  # List of knowledge bases to search
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    action_rounds_budget: int = 0  # Budget for BFS agent action rounds
    current_round: int = 0  # Current action round for BFS agent

class DFSAgentState(BaseModel):
    """State for the depth-first search agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    search_target: str = ""
    knowledge_bases: List[str] = []  # List of knowledge bases to search
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    action_rounds_budget: int = 0  # Budget for DFS agent action rounds
    current_round: int = 0  # Current action round for DFS agent
