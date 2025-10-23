from biodsa.sandbox.execution import ExecutionResults
from typing import List, Dict
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

class DeepEvidenceExecutionResults(ExecutionResults):
    """Execution results for the deep evidence agent."""
    def __init__(self,
        message_history: List[Dict[str, str]], 
        code_execution_results: List[Dict[str, str]], 
        final_response: str,
        sandbox: ExecutionSandboxWrapper = None,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0
    ):
        super().__init__(message_history, code_execution_results, final_response, sandbox)
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
