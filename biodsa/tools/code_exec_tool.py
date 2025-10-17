from langchain.tools import BaseTool
from biodsa.utils.token_utils import truncate_middle_tokens
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

CODE_EXECUTION_TOOL_DESCRIPTION = """
Execute code to answer the user's question. When you use this tool, you should use `print` to print the result, otherwise you will not be able to see the result. For example, use `print(df)` to print the dataframe, do not use `df.head()` to print the dataframe.
You should avoid adding any comments in the code to reduce the size of the code.
"""

class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = CODE_EXECUTION_TOOL_DESCRIPTION
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
        stdout = truncate_middle_tokens(output, 4096)
        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "artifacts": artifacts,
            "running_time": running_time,
            "peak_memory_mb": peak_memory_mb,
        }