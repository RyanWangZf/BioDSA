"""
File writing and editing tools for workspace-sandboxed agents.

These tools provide a safe, reliable way to create and edit files inside a
workspace directory — either on the **local filesystem** or inside a
**Docker container** (when a sandbox is provided).

Unlike bash heredoc (``cat > file << 'EOF'``), these tools handle arbitrary
file content — including Python code with ``...``, special characters, or
multi-line strings — without escaping issues.
"""

from __future__ import annotations

import io
import logging
import os
import re
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Path helpers
# ------------------------------------------------------------------ #

def _validate_rel_path(rel_path: str) -> tuple[bool, str, str]:
    """
    Validate a workspace-relative path (mode-agnostic).

    Returns (ok, error_message, cleaned_relative_path).
    """
    rel_path = rel_path.strip().strip("/")
    if not rel_path:
        return False, "Error: empty file path.", ""
    parts = Path(rel_path).parts
    if ".." in parts:
        return False, f"Error: '..' not allowed in path: {rel_path}", ""
    return True, "", rel_path


def _resolve_local(rel_path: str, data_root: Path) -> tuple[bool, str, Path]:
    """Resolve a relative path to a local absolute path inside data_root."""
    ok, err, cleaned = _validate_rel_path(rel_path)
    if not ok:
        return False, err, data_root
    resolved = (data_root / cleaned).resolve()
    try:
        resolved.relative_to(data_root.resolve())
    except ValueError:
        return False, f"Error: path escapes workspace: {rel_path}", data_root
    return True, "", resolved


# ------------------------------------------------------------------ #
# Docker helpers
# ------------------------------------------------------------------ #

def _docker_write(sandbox: object, container_path: str, content: str) -> str:
    """Write string content to a file inside a Docker container."""
    container = sandbox.container
    if container is None:
        return "Error: Docker container is not running."

    # Ensure parent directory exists
    parent = os.path.dirname(container_path)
    if parent:
        container.exec_run(f"mkdir -p {parent}")

    # Upload via tar archive
    content_bytes = content.encode("utf-8")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        info = tarfile.TarInfo(name=os.path.basename(container_path))
        info.size = len(content_bytes)
        info.mtime = int(datetime.now().timestamp())
        tar.addfile(info, io.BytesIO(content_bytes))
    tar_stream.seek(0)

    target_dir = parent if parent else "/"
    container.put_archive(target_dir, tar_stream)
    return ""


def _docker_read(sandbox: object, container_path: str) -> tuple[bool, str]:
    """Read a file from a Docker container. Returns (ok, content_or_error)."""
    container = sandbox.container
    if container is None:
        return False, "Error: Docker container is not running."
    try:
        bits, _ = container.get_archive(container_path)
        raw = b"".join(bits)
        tar_stream = io.BytesIO(raw)
        with tarfile.open(fileobj=tar_stream) as tar:
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f is not None:
                    return True, f.read().decode("utf-8", errors="replace")
        return False, f"Error: could not extract {container_path} from archive."
    except Exception as e:
        return False, f"Error reading {container_path}: {e}"


# ------------------------------------------------------------------ #
# WriteFileTool
# ------------------------------------------------------------------ #

class WriteFileInput(BaseModel):
    file_path: str = Field(
        description=(
            "Path to the file to write (relative to workspace). "
            "Parent directories are created automatically."
        )
    )
    content: str = Field(
        description="The full content to write to the file."
    )
    mode: str = Field(
        default="overwrite",
        description=(
            "'overwrite' (default) replaces the file entirely. "
            "'append' adds content to the end of an existing file."
        ),
    )


class WriteFileTool(BaseTool):
    """
    Write content to a file inside the workspace.

    Operates on the **local filesystem** (when ``data_root`` is set) or
    inside a **Docker container** (when ``sandbox`` is set).
    Creates parent directories automatically.
    """

    name: str = "write_file"
    description: str = (
        "Write content to a file in the workspace. "
        "Use mode='overwrite' (default) to create or replace a file, "
        "or mode='append' to add to the end. Parent directories are "
        "created automatically. Preferred over bash for writing Python "
        "code and multi-line content."
    )
    args_schema: Type[BaseModel] = WriteFileInput
    data_root: Optional[Path] = None
    sandbox: object = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        data_root: Optional[Path] = None,
        sandbox: object = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if data_root is not None:
            self.data_root = Path(data_root).resolve()
        self.sandbox = sandbox

    def _run(self, file_path: str, content: str, mode: str = "overwrite") -> str:
        if self.sandbox is not None:
            return self._run_docker(file_path, content, mode)
        return self._run_local(file_path, content, mode)

    # -- local --------------------------------------------------------- #

    def _run_local(self, file_path: str, content: str, mode: str) -> str:
        ok, err, resolved = _resolve_local(file_path, self.data_root)
        if not ok:
            return err
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            if mode == "append":
                with open(resolved, "a", encoding="utf-8") as f:
                    f.write(content)
                return f"Appended {len(content)} chars to {file_path}."
            else:
                with open(resolved, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Wrote {len(content)} chars to {file_path}."
        except Exception as e:
            return f"Error writing {file_path}: {e}"

    # -- docker -------------------------------------------------------- #

    def _run_docker(self, file_path: str, content: str, mode: str) -> str:
        ok, err, cleaned = _validate_rel_path(file_path)
        if not ok:
            return err
        container_path = f"{self.sandbox.workdir}/{cleaned}"

        if mode == "append":
            # Read existing content first
            read_ok, existing = _docker_read(self.sandbox, container_path)
            if read_ok:
                content = existing + content
            # If file doesn't exist yet, that's fine — just write content

        err = _docker_write(self.sandbox, container_path, content)
        if err:
            return err
        verb = "Appended" if mode == "append" else "Wrote"
        return f"{verb} {len(content)} chars to {file_path}."


# ------------------------------------------------------------------ #
# EditFileTool
# ------------------------------------------------------------------ #

class EditFileInput(BaseModel):
    file_path: str = Field(
        description="Path to the file to edit (relative to workspace)."
    )
    old_text: str = Field(
        description=(
            "The exact text to find in the file.  Must match exactly "
            "(including whitespace/indentation) unless use_regex=True."
        )
    )
    new_text: str = Field(
        description="The replacement text."
    )
    use_regex: bool = Field(
        default=False,
        description=(
            "If True, old_text is treated as a Python regex pattern "
            "and new_text can use backreferences (\\1, \\2, etc.)."
        ),
    )
    count: int = Field(
        default=0,
        description=(
            "Max replacements. 0 (default) = replace all occurrences. "
            "1 = replace only the first occurrence."
        ),
    )


class EditFileTool(BaseTool):
    """
    Edit a file by replacing text (exact match or regex).

    Operates on the **local filesystem** or inside a **Docker container**.
    """

    name: str = "edit_file"
    description: str = (
        "Edit a file by replacing text. Provide old_text (the exact text "
        "to find) and new_text (the replacement). Set use_regex=True to "
        "use regex patterns. Set count=1 to replace only the first match, "
        "or count=0 (default) for all matches."
    )
    args_schema: Type[BaseModel] = EditFileInput
    data_root: Optional[Path] = None
    sandbox: object = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        data_root: Optional[Path] = None,
        sandbox: object = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if data_root is not None:
            self.data_root = Path(data_root).resolve()
        self.sandbox = sandbox

    def _run(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        use_regex: bool = False,
        count: int = 0,
    ) -> str:
        if self.sandbox is not None:
            return self._run_docker(file_path, old_text, new_text, use_regex, count)
        return self._run_local(file_path, old_text, new_text, use_regex, count)

    # -- shared logic -------------------------------------------------- #

    @staticmethod
    def _apply_edit(
        original: str,
        old_text: str,
        new_text: str,
        use_regex: bool,
        count: int,
        file_path: str,
    ) -> tuple[bool, str, str, int]:
        """
        Apply the edit to *original*.

        Returns (ok, error_or_empty, new_content, n_replacements).
        """
        if use_regex:
            try:
                pattern = re.compile(old_text, re.DOTALL)
            except re.error as e:
                return False, f"Error: invalid regex: {e}", "", 0
            new_content, n = pattern.subn(new_text, original, count=count or 0)
        else:
            if old_text not in original:
                preview = original[:500] + ("..." if len(original) > 500 else "")
                return (
                    False,
                    f"Error: old_text not found in {file_path}.\n"
                    f"File starts with:\n{preview}",
                    "",
                    0,
                )
            if count == 1:
                new_content = original.replace(old_text, new_text, 1)
                n = 1
            elif count == 0:
                n = original.count(old_text)
                new_content = original.replace(old_text, new_text)
            else:
                new_content = original
                n = 0
                for _ in range(count):
                    if old_text in new_content:
                        new_content = new_content.replace(old_text, new_text, 1)
                        n += 1
                    else:
                        break

        if new_content == original:
            return (
                False,
                f"No changes made to {file_path} (old_text not found "
                f"or identical replacement).",
                "",
                0,
            )
        return True, "", new_content, n

    # -- local --------------------------------------------------------- #

    def _run_local(
        self, file_path: str, old_text: str, new_text: str,
        use_regex: bool, count: int,
    ) -> str:
        ok, err, resolved = _resolve_local(file_path, self.data_root)
        if not ok:
            return err
        if not resolved.exists():
            return f"Error: file not found: {file_path}"
        try:
            original = resolved.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading {file_path}: {e}"

        ok, err, new_content, n = self._apply_edit(
            original, old_text, new_text, use_regex, count, file_path,
        )
        if not ok:
            return err
        try:
            resolved.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return f"Error writing {file_path}: {e}"
        return f"Edited {file_path}: {n} replacement(s) made."

    # -- docker -------------------------------------------------------- #

    def _run_docker(
        self, file_path: str, old_text: str, new_text: str,
        use_regex: bool, count: int,
    ) -> str:
        ok, err, cleaned = _validate_rel_path(file_path)
        if not ok:
            return err
        container_path = f"{self.sandbox.workdir}/{cleaned}"

        read_ok, original = _docker_read(self.sandbox, container_path)
        if not read_ok:
            return original  # error message

        ok, err, new_content, n = self._apply_edit(
            original, old_text, new_text, use_regex, count, file_path,
        )
        if not ok:
            return err

        write_err = _docker_write(self.sandbox, container_path, new_content)
        if write_err:
            return write_err
        return f"Edited {file_path}: {n} replacement(s) made."
