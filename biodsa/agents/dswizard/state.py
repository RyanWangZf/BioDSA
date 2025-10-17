from pydantic import BaseModel
from typing import List, Annotated, Sequence
from langgraph.graph.message import add_messages, BaseMessage

from biodsa.agents.state import CodeExecutionResult

class DSWizardAgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
    analysis_plan: str = ""