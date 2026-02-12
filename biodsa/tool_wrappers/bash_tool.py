"""
Bash-in-workspace tool wrapper.

Runs a bash command inside a workspace directory — either on the **local
filesystem** or inside a **Docker container** (when a sandbox is provided).
Path-traversal via ``../`` is blocked.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

# Regex that matches path-traversal patterns:
#   ../ or /.. or /../ at the start, end, or surrounded by separators
_PATH_TRAVERSAL_RE = re.compile(
    r"(?:^|[\s;|&\"'])\.\.(?:[/\s;|&\"']|$)"
)


class BashInWorkspaceInput(BaseModel):
    command: str = Field(
        description=(
            "Bash command to run in the workspace directory. "
            "Use for: ls, cat, head, mkdir, grep, mv, cp, etc. "
            "Paths are relative to the workspace. "
            "Do not use '..' path segments or absolute paths."
        )
    )


class BashInWorkspaceTool(BaseTool):
    """
    Run a bash command inside a workspace directory.

    When a ``sandbox`` (``ExecutionSandboxWrapper``) is provided the
    command runs inside the Docker container.  Otherwise it runs locally
    with the working directory set to ``data_root``.

    Path-traversal patterns (``../``) are blocked in both modes.
    """

    name: str = "bash_in_workspace"
    description: str = (
        "Run a bash command in the workspace. Use for: ls, cat, head, "
        "mkdir -p, grep, mv, cp, running scripts. For writing multi-line "
        "files (Python code, Markdown, etc.) prefer the write_file tool. "
        "Paths must be relative; no '..' path segments."
    )
    args_schema: Type[BaseModel] = BashInWorkspaceInput

    # Exactly one of these should be set:
    data_root: Optional[Path] = None      # local mode
    sandbox: object = None                 # Docker mode (ExecutionSandboxWrapper)
    timeout_seconds: int = 60

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        data_root: Optional[Path] = None,
        sandbox: object = None,
        timeout_seconds: int = 60,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if data_root is not None:
            self.data_root = Path(data_root).resolve()
        self.sandbox = sandbox
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _get_workdir(self) -> str:
        """Return the working directory path (local or in-container)."""
        if self.sandbox is not None:
            return self.sandbox.workdir
        if self.data_root is not None:
            return str(self.data_root)
        return "."

    def _execute_local(self, command: str) -> str:
        """Execute command locally via subprocess."""
        cwd = str(self.data_root) if self.data_root else "."
        if self.data_root and not self.data_root.exists():
            return (
                f"$ {command}\n\n"
                f"Error: workspace does not exist: {self.data_root}"
            )
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            lines = [f"$ {command}"]
            if out:
                lines.append(f"stdout:\n{out}")
            if err:
                lines.append(f"stderr:\n{err}")
            lines.append(f"returncode: {result.returncode}")
            return "\n\n".join(lines)
        except subprocess.TimeoutExpired:
            return f"$ {command}\n\nError: command timed out."
        except Exception as e:
            return f"$ {command}\n\nError: {e}"

    def _execute_in_sandbox(self, command: str) -> str:
        """Execute command inside the Docker container."""
        try:
            container = self.sandbox.container
            if container is None:
                return (
                    f"$ {command}\n\n"
                    f"Error: Docker container is not running."
                )
            exit_code, output = container.exec_run(
                f"bash -c {_shell_quote(command)}",
                workdir=self.sandbox.workdir,
            )
            stdout = output.decode("utf-8", errors="replace").strip()
            lines = [f"$ {command}"]
            if stdout:
                lines.append(f"stdout:\n{stdout}")
            lines.append(f"returncode: {exit_code}")
            return "\n\n".join(lines)
        except Exception as e:
            logger.error("Sandbox bash execution failed: %s", e)
            return f"$ {command}\n\nError: {e}"

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def _run(self, command: str) -> str:
        # Check for path-traversal patterns (but allow "..." in Python code)
        if _PATH_TRAVERSAL_RE.search(command):
            return (
                f"$ {command}\n\n"
                f"Error: '..' path traversal not allowed; "
                f"paths must stay inside the workspace."
            )

        if self.sandbox is not None:
            return self._execute_in_sandbox(command)
        return self._execute_local(command)


def _shell_quote(s: str) -> str:
    """Wrap a string in single-quotes safe for bash -c."""
    # Replace ' with '"'"' so bash handles it correctly
    return "'" + s.replace("'", "'\"'\"'") + "'"
