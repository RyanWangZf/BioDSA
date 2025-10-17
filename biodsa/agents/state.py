from pydantic import BaseModel, Field
from typing import List, Literal, Annotated, Sequence, TypedDict, Dict, Any

from langgraph.graph.message import add_messages, BaseMessage

class CodeExecutionResult(BaseModel):
    code: str
    console_output: str
    running_time: float
    peak_memory: float

    def __str__(self):
        return f"Code: {self.code}\nConsole Output: {self.console_output}\nRunning Time: {self.running_time}\nPeak Memory: {self.peak_memory}"

class AgentState(BaseModel):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []