from langchain.tools import BaseTool
from biodsa.utils.token_utils import truncate_middle_tokens
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tool_wrappers.utils import run_python_repl

CODE_EXECUTION_TOOL_DESCRIPTION = """
Execute code to answer the user's question. When you use this tool, you should use `print` to print the result, otherwise you will not be able to see the result. For example, use `print(df)` to print the dataframe, do not use `df.head()` to print the dataframe.
You should avoid adding any comments in the code to reduce the size of the code.
"""

class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = CODE_EXECUTION_TOOL_DESCRIPTION
    sandbox: ExecutionSandboxWrapper = None
    max_output_tokens: int = 4096

    def __init__(self, sandbox: ExecutionSandboxWrapper = None, max_output_tokens: int = 4096):
        super().__init__()
        self.sandbox = sandbox
        self.max_output_tokens = max_output_tokens

    def _run(self, code: str) -> str:
        """
        Execute the provided Python code in the sandbox, or locally if no sandbox is available.
        
        Args:
            code: Python code to execute
            
        Returns:
            Formatted string with executed code, output, and execution metrics
        """
        if self.sandbox is not None:
            # Execute the code in sandbox
            exit_code, output, artifacts, running_time, peak_memory_mb = self.sandbox.execute(
                language="python",
                code=code
            )
            
            # Truncate output if too long
            stdout = truncate_middle_tokens(output, self.max_output_tokens)
            
            # Format result to match other tools
            result = f"### Executed Code:\n```python\n{code}\n```\n\n"
            result += f"### Output:\n```\n{stdout}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory_mb:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            if artifacts:
                result += f"\n\n**Artifacts:** {len(artifacts)} file(s) generated"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code)
            
            # Truncate output if too long
            stdout = truncate_middle_tokens(output, self.max_output_tokens)
            
            # Format result to match other tools
            result = f"### Executed Code:\n```python\n{code}\n```\n\n"
            result += f"### Output:\n```\n{stdout}\n```\n\n"
            
            return result