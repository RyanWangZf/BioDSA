"""
Code-execution tool wrapper.

Executes Python (or R) code either inside a Docker sandbox
(``ExecutionSandboxWrapper``) or locally via a persistent REPL.
The Docker path provides full process isolation, artifact collection,
and memory monitoring.
"""

from __future__ import annotations

import logging
from typing import Optional, Type

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.utils.token_utils import truncate_middle_tokens
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tool_wrappers.utils import run_python_repl

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Input schema
# ------------------------------------------------------------------ #

class CodeExecutionInput(BaseModel):
    code: str = Field(
        description=(
            "Python code to execute. Use print() to surface results — "
            "values that are not printed will not appear in the output."
        )
    )
    language: str = Field(
        default="python",
        description="Language to execute: 'python' (default) or 'r'.",
    )


# ------------------------------------------------------------------ #
# Tool
# ------------------------------------------------------------------ #

CODE_EXECUTION_TOOL_DESCRIPTION = (
    "Execute code in an isolated environment. Use print() to surface "
    "results — values that are not printed will not appear in the output. "
    "Avoid adding comments to reduce code size. "
    "The environment persists across calls (variables survive between "
    "invocations)."
)


class CodeExecutionTool(BaseTool):
    """
    Execute code inside a Docker sandbox or locally.

    When a ``sandbox`` (``ExecutionSandboxWrapper``) is provided the code
    runs in an isolated Docker container with artifact collection and
    memory monitoring.  When *no* sandbox is available the tool falls back
    to an in-process Python REPL (``run_python_repl``).
    """

    name: str = "code_execution"
    description: str = CODE_EXECUTION_TOOL_DESCRIPTION
    args_schema: Type[BaseModel] = CodeExecutionInput
    sandbox: Optional[ExecutionSandboxWrapper] = None
    max_output_tokens: int = 4096
    timeout_seconds: int = 300  # 5 min default for Docker execution

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        sandbox: Optional[ExecutionSandboxWrapper] = None,
        max_output_tokens: int = 4096,
        timeout_seconds: int = 300,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds

    # -------------------------------------------------------------- #
    # Helpers
    # -------------------------------------------------------------- #

    def _sandbox_is_alive(self) -> bool:
        """Check that the sandbox container is still running."""
        if self.sandbox is None:
            return False
        try:
            if not self.sandbox.exists():
                return False
            # Quick health-check: container reachable?
            self.sandbox.container.reload()
            return self.sandbox.container.status == "running"
        except Exception:
            return False

    def _execute_in_sandbox(self, code: str, language: str) -> str:
        """Execute code inside the Docker sandbox."""
        try:
            exit_code, output, artifacts, running_time, peak_memory_mb = (
                self.sandbox.execute(language=language, code=code)
            )
        except Exception as e:
            logger.error("Sandbox execution failed: %s", e)
            return (
                f"### Executed Code:\n```{language}\n{code}\n```\n\n"
                f"### Error:\n```\nSandbox execution failed: {e}\n```\n\n"
                f"*The Docker container may have stopped or become "
                f"unreachable. Consider restarting the sandbox.*"
            )

        stdout = truncate_middle_tokens(output, self.max_output_tokens)

        result = f"### Executed Code:\n```{language}\n{code}\n```\n\n"
        result += f"### Output:\n```\n{stdout}\n```\n\n"
        result += (
            f"*Execution time: {running_time:.2f}s, "
            f"Peak memory: {peak_memory_mb:.2f}MB*"
        )

        if exit_code != 0:
            result += (
                f"\n\n⚠️ **Warning:** Code exited with non-zero "
                f"status ({exit_code})"
            )

        if artifacts:
            result += (
                f"\n\n**Artifacts:** {len(artifacts)} file(s) generated"
            )

        return result

    def _execute_locally(self, code: str, language: str) -> str:
        """Fallback: execute Python code in a local in-process REPL."""
        if language != "python":
            return (
                f"### Error:\n```\nLocal execution only supports Python. "
                f"Requested language: {language}. "
                f"Provide a Docker sandbox for {language} support.\n```"
            )
        try:
            output = run_python_repl(code)
        except Exception as e:
            output = f"Error: {e}"

        stdout = truncate_middle_tokens(output, self.max_output_tokens)

        result = f"### Executed Code:\n```python\n{code}\n```\n\n"
        result += f"### Output:\n```\n{stdout}\n```"
        return result

    # -------------------------------------------------------------- #
    # Public interface
    # -------------------------------------------------------------- #

    def _run(self, code: str, language: str = "python") -> str:
        """
        Execute the provided code.

        Tries the Docker sandbox first; if the sandbox is unavailable or
        the container has stopped, falls back to local execution with a
        warning.
        """
        if self._sandbox_is_alive():
            return self._execute_in_sandbox(code, language)

        if self.sandbox is not None:
            # Sandbox was configured but container is not running
            logger.warning(
                "Sandbox container is not running — falling back to "
                "local execution."
            )

        return self._execute_locally(code, language)
