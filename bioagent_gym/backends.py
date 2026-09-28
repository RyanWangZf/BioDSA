from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from .errors import HarnessError


@dataclass
class ProcessOutcome:
    exit_code: int | None
    timed_out: bool
    cancelled: bool
    started_at: str
    ended_at: str
    duration_seconds: float


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


class LocalBackend:
    """Development backend. It is process isolation, not a security boundary."""

    def __init__(self) -> None:
        self.process: subprocess.Popen[bytes] | None = None
        self._stdout: IO[bytes] | None = None
        self._stderr: IO[bytes] | None = None
        self._cancelled = False

    def start(self, argv: list[str], cwd: Path, env: dict[str, str], stdout: Path, stderr: Path) -> None:
        stdout.parent.mkdir(parents=True, exist_ok=True)
        self._stdout = stdout.open("wb")
        self._stderr = stderr.open("wb")
        self.process = subprocess.Popen(
            argv,
            cwd=cwd,
            env={**os.environ, **env},
            stdout=self._stdout,
            stderr=self._stderr,
            start_new_session=True,
        )

    def cancel(self) -> None:
        self._cancelled = True
        self._terminate_group()

    def _terminate_group(self) -> None:
        if not self.process or self.process.poll() is not None:
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=2)
        except ProcessLookupError:
            pass

    def wait(self, timeout: float) -> ProcessOutcome:
        if self.process is None:
            raise HarnessError("backend was not started")
        started_text = utc_now()
        started = time.monotonic()
        timed_out = False
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._terminate_group()
        finally:
            self.cleanup()
        return ProcessOutcome(
            exit_code=self.process.returncode,
            timed_out=timed_out,
            cancelled=self._cancelled,
            started_at=started_text,
            ended_at=utc_now(),
            duration_seconds=round(time.monotonic() - started, 6),
        )

    def cleanup(self) -> None:
        for handle in (self._stdout, self._stderr):
            if handle:
                handle.close()
        self._stdout = self._stderr = None


class DockerBackend(LocalBackend):
    def __init__(self, manifest: dict, request_dir: Path, output_dir: Path):
        super().__init__()
        if not shutil.which("docker"):
            raise HarnessError("docker executable is unavailable")
        self.manifest = manifest
        self.request_dir = request_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.container_name = f"bioagent-gym-{uuid.uuid4().hex[:16]}"

    def agent_argv(self, extra: list[str]) -> list[str]:
        docker = self.manifest.get("docker", {})
        image = docker.get("image")
        command = docker.get("command", [])
        if not image or not command:
            raise HarnessError("docker backend requires docker.image and docker.command")
        argv = ["docker", "run", "--name", self.container_name, "--rm"]
        argv += ["--mount", f"type=bind,src={self.request_dir},dst=/input,readonly"]
        argv += ["--mount", f"type=bind,src={self.output_dir},dst=/output"]
        # `--env NAME` copies the value from the docker CLI environment without
        # placing the secret in argv, manifests, requests, or run records.
        for name in self.manifest.get("required_env", []):
            argv += ["--env", name]
        resources = self.manifest.get("resources", {})
        if resources.get("cpus") is not None:
            argv += ["--cpus", str(resources["cpus"])]
        if resources.get("memory"):
            argv += ["--memory", str(resources["memory"])]
        if resources.get("gpus"):
            argv += ["--gpus", str(resources["gpus"])]
        if not resources.get("network", False):
            argv += ["--network", "none"]
        argv += [image, *command, *extra]
        return argv

    def _terminate_group(self) -> None:
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        super()._terminate_group()

    def cleanup(self) -> None:
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        super().cleanup()
