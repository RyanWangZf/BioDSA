from pydantic import BaseModel, Field
from typing import List, Literal, Annotated, Sequence, TypedDict, Dict, Any

from langgraph.graph.message import add_messages, BaseMessage
# from langgraph.managed import IsLastStep, RemainingSteps

# class UserRequest(TypedDict):
#     input_query: str
#     dataset_paths: str
#     dataset_schema: str

# class FinalResponse(BaseModel):
#     final_answer: Literal["True", "False", "Not Verifiable"]
#     executions: List[Dict[str, Any]]
#     analysis: List[str]
#     def __str__(self):
#         return f"Final Answer: {self.final_answer}\nAnalysis: {"\n".join(self.analysis)}"

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