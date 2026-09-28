from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
import uuid
import json
import threading
from contextlib import suppress
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
        try:
            self._stdout = stdout.open("wb")
            self._stderr = stderr.open("wb")
            inherited = {name: os.environ[name] for name in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR") if name in os.environ}
            self.process = subprocess.Popen(
                argv,
                cwd=cwd,
                env={**inherited, **env},
                stdout=self._stdout,
                stderr=self._stderr,
                start_new_session=True,
            )
        except BaseException:
            self.cleanup()
            raise

    def cancel(self) -> None:
        self._cancelled = True
        try:
            self._terminate_group()
        finally:
            self.cleanup()

    def _terminate_group(self) -> None:
        if not self.process or self.process.poll() is not None:
            return
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(self.process.pid, signal.SIGTERM)
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError, PermissionError):
                os.killpg(self.process.pid, signal.SIGKILL)
            with suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=2)

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
        except BaseException:
            self._cancelled = True
            self._terminate_group()
            raise
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
                with suppress(Exception):
                    handle.close()
        self._stdout = self._stderr = None


class DockerBackend(LocalBackend):
    def __init__(self, manifest: dict, request_dir: Path, workspace_dir: Path, output_dir: Path, network_mode: str = "internet", channel_dir: Path | None = None, env_names: list[str] | None = None):
        super().__init__()
        if not shutil.which("docker"):
            raise HarnessError("docker executable is unavailable")
        self.manifest = manifest
        self.request_dir = request_dir.resolve()
        self.workspace_dir = workspace_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.network_mode = network_mode
        self.channel_dir = channel_dir.resolve() if channel_dir else None
        self.env_names = env_names or list(manifest.get("required_env", []))
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
        argv += ["--mount", f"type=bind,src={self.workspace_dir},dst=/workspace"]
        if self.channel_dir:
            argv += ["--mount", f"type=bind,src={self.channel_dir},dst=/sandbox-channel"]
        argv += ["--workdir", "/workspace"]
        # `--env NAME` copies the value from the docker CLI environment without
        # placing the secret in argv, manifests, requests, or run records.
        for name in self.env_names:
            argv += ["--env", name]
        resources = self.manifest.get("resources", {})
        if resources.get("cpus") is not None:
            argv += ["--cpus", str(resources["cpus"])]
        if resources.get("memory"):
            argv += ["--memory", str(resources["memory"])]
        if resources.get("gpus"):
            argv += ["--gpus", str(resources["gpus"])]
        if self.network_mode == "none":
            argv += ["--network", "none"]
        argv += [image, *command, *extra]
        return argv

    def _terminate_group(self) -> None:
        with suppress(Exception):
            subprocess.run(
                ["docker", "rm", "-f", self.container_name], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=False,
            )
        super()._terminate_group()

    def cleanup(self) -> None:
        with suppress(Exception):
            subprocess.run(
                ["docker", "rm", "-f", self.container_name], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=False,
            )
        super().cleanup()


class SandboxContainer:
    """Host-managed generated-code container using a shared file channel."""

    def __init__(self, manifest: dict, workspace_dir: Path, channel_dir: Path, network_mode: str, env_names: list[str], logs_dir: Path | None = None, startup_timeout: float = 10):
        if not shutil.which("docker"):
            raise HarnessError("docker executable is unavailable")
        self.manifest = manifest
        self.workspace_dir = workspace_dir.resolve()
        self.channel_dir = channel_dir.resolve()
        self.network_mode = network_mode
        self.env_names = env_names
        self.container_name = f"bioagent-gym-sandbox-{uuid.uuid4().hex[:16]}"
        self.started = False
        self.logs_dir = logs_dir.resolve() if logs_dir else self.channel_dir
        self.startup_timeout = startup_timeout
        self._stop_monitor = threading.Event()
        self._monitor: threading.Thread | None = None

    def start(self) -> None:
        docker = self.manifest["sandbox"]["docker"]
        # Keep the stopped container until cleanup so startup/worker logs remain
        # available after an early exit.
        argv = ["docker", "run", "-d", "--name", self.container_name]
        argv += ["--mount", f"type=bind,src={self.workspace_dir},dst=/workspace"]
        argv += ["--mount", f"type=bind,src={self.channel_dir},dst=/channel"]
        argv += ["--workdir", "/workspace"]
        if self.network_mode == "none": argv += ["--network", "none"]
        for name in self.env_names: argv += ["--env", name]
        resources = self.manifest["sandbox"].get("resources", {})
        if resources.get("cpus") is not None: argv += ["--cpus", str(resources["cpus"])]
        if resources.get("memory"): argv += ["--memory", str(resources["memory"])]
        if resources.get("gpus"): argv += ["--gpus", str(resources["gpus"])]
        argv += [docker["image"], *docker["command"], "--channel", "/channel"]
        completed = subprocess.run(argv, capture_output=True, text=True)
        if completed.returncode:
            raise HarnessError(f"sandbox container failed to start: {completed.stderr.strip()}")
        self.started = True
        deadline = time.monotonic() + self.startup_timeout
        ready = self.channel_dir / "ready.json"
        while time.monotonic() < deadline:
            if ready.is_file():
                self._monitor = threading.Thread(target=self._monitor_worker, daemon=True); self._monitor.start()
                return
            status = subprocess.run(["docker", "inspect", "--format", "{{.State.Running}} {{.State.ExitCode}}", self.container_name], capture_output=True, text=True)
            if status.returncode or not status.stdout.startswith("true "):
                detail = self._capture_logs()
                self.cleanup()
                raise HarnessError(f"sandbox worker exited before ready: {status.stdout.strip() or status.stderr.strip()}; logs: {detail}")
            time.sleep(.05)
        detail = self._capture_logs(); self.cleanup()
        raise HarnessError(f"sandbox worker did not become ready within {self.startup_timeout:g}s; logs: {detail}")

    def _capture_logs(self) -> str:
        completed = subprocess.run(["docker", "logs", self.container_name], capture_output=True, text=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "sandbox.stdout.log").write_text(completed.stdout)
        (self.logs_dir / "sandbox.stderr.log").write_text(completed.stderr)
        return (completed.stderr or completed.stdout).strip()[-1000:] or "<empty>"

    def _monitor_worker(self) -> None:
        while not self._stop_monitor.wait(.1):
            status = subprocess.run(["docker", "inspect", "--format", "{{.State.Running}} {{.State.ExitCode}}", self.container_name], capture_output=True, text=True)
            if status.returncode or not status.stdout.startswith("true "):
                detail = self._capture_logs()
                temporary = self.channel_dir / ".worker-failure.tmp"
                temporary.write_text(json.dumps({"code":"worker_exited","message":detail,"container_status":status.stdout.strip()}))
                os.replace(temporary, self.channel_dir / "worker-failure.json")
                return

    def cleanup(self) -> None:
        if not self.started: return
        self._stop_monitor.set()
        self._capture_logs()
        with suppress(Exception):
            subprocess.run(["docker", "rm", "-f", self.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
        self.started = False
        if self._monitor and self._monitor is not threading.current_thread(): self._monitor.join(timeout=1)
