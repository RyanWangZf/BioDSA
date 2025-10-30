from pydantic import BaseModel
from typing import List, Annotated, Sequence
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
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    subgraph_tool_call_ids: List[str] = []

class BFSAgentState(BaseModel):
    """State for the breadth-first search agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    search_target: str = ""
    knowledge_bases: List[str] = []  # List of knowledge bases to search
    total_input_tokens: int = 0
    total_output_tokens: int = 0

class DFSAgentState(BaseModel):
    """State for the depth-first search agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    search_target: str = ""
    knowledge_base: str = ""  # Single knowledge base to search
    total_input_tokens: int = 0
    total_output_tokens: int = 0