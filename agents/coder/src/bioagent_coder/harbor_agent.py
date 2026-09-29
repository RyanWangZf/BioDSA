from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import override

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class CoderOptions(AgentOptions):
    provider: str = "mock"
    endpoint: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 60
    max_attempts: int = 2
    max_tokens: int = 2000
    reasoning_effort: str | None = None
    item_ids: list[str] = []
    item_timeout_seconds: float = 300


class CoderHarborAgent(BaseAgent):
    """Harbor adapter; the Coder workflow and generated code run in the trial."""

    options_model = CoderOptions

    @staticmethod
    @override
    def name() -> str:
        return "bioagent-coder"

    @override
    def version(self) -> str:
        return "0.2.0"

    @override
    async def setup(self, environment: BaseEnvironment) -> None:
        stage = self.logs_dir / "package-stage"
        if stage.exists():
            shutil.rmtree(stage)
        package = stage / "bioagent_coder"
        shutil.copytree(Path(__file__).resolve().parent, package)
        await environment.upload_dir(stage, "/tmp/bioagent-coder")
        result = await environment.exec(
            "python3 -c \"import shutil,site; shutil.copytree('/tmp/bioagent-coder/bioagent_coder', site.getsitepackages()[0]+'/bioagent_coder', dirs_exist_ok=True)\"",
            user="root",
            timeout_sec=180,
        )
        if result.return_code:
            raise RuntimeError(f"Coder install failed: {result.stderr or result.stdout}")

    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        request = self.logs_dir / "harbor-input.json"
        config = self.options.model_dump()
        config.update({
            "model": self.model_name,
            "execution_environment": {"backend": "local_subprocess", "timeout_seconds": config.pop("timeout_seconds")},
        })
        item_ids = config.pop("item_ids")
        item_timeout_seconds = config.pop("item_timeout_seconds")
        request.write_text(json.dumps({"instruction": instruction, "config": config, "item_ids": item_ids, "item_timeout_seconds": item_timeout_seconds}))
        await environment.upload_file(request, "/tmp/bioagent-input.json")
        result = await environment.exec(
            "python3 -m bioagent_coder.harbor_runner /tmp/bioagent-input.json",
            cwd="/app",
        )
        (self.logs_dir / "agent.stdout").write_text(result.stdout or "")
        (self.logs_dir / "agent.stderr").write_text(result.stderr or "")
        if result.return_code:
            raise RuntimeError(f"Coder workflow failed ({result.return_code}): {result.stderr or result.stdout}")
        context.metadata = {"submission_dir": "/app/submission"}
