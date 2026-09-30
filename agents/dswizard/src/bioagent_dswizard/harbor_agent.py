from __future__ import annotations

import json
from bioagent_harbor_runtime import install_command, stage_agent
from pathlib import Path
from typing import override

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class DSWizardOptions(AgentOptions):
    provider: str = "mock"
    endpoint: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 90
    max_attempts: int = 2
    max_tokens: int = 2000
    reasoning_effort: str | None = None
    item_ids: list[str] | None = None
    item_timeout_seconds: float = 300


class DSWizardHarborAgent(BaseAgent):
    options_model = DSWizardOptions

    @staticmethod
    @override
    def name() -> str:
        return "bioagent-dswizard"

    @override
    def version(self) -> str:
        return "0.2.0"

    @override
    async def setup(self, environment: BaseEnvironment) -> None:
        stage = self.logs_dir / "package-stage"
        stage_agent(Path(__file__).resolve().parent, "bioagent-dswizard", "bioagent_dswizard", stage)
        await environment.upload_dir(stage, "/tmp/bioagent-dswizard")
        result = await environment.exec(install_command("/tmp/bioagent-dswizard", "/opt/bioagent-dswizard", "bioagent_dswizard"), user="root", timeout_sec=180)
        if result.return_code:
            raise RuntimeError(f"DSWizard install failed: {result.stderr or result.stdout}")

    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        request = self.logs_dir / "harbor-input.json"
        config = self.options.model_dump()
        config.update({"model": self.model_name, "execution_environment": {"backend": "local_subprocess", "timeout_seconds": config.pop("timeout_seconds"), "python_executable": "/usr/local/bin/python3"}})
        item_ids = config.pop("item_ids")
        item_timeout_seconds = config.pop("item_timeout_seconds")
        payload={"instruction": instruction, "config": config, "item_timeout_seconds": item_timeout_seconds}
        if item_ids is not None: payload["item_ids"]=item_ids
        request.write_text(json.dumps(payload))
        await environment.upload_file(request, "/tmp/bioagent-input.json")
        result = await environment.exec("/opt/bioagent-dswizard/bin/python -m bioagent_dswizard.harbor_runner /tmp/bioagent-input.json", cwd="/app")
        (self.logs_dir / "agent.stdout").write_text(result.stdout or "")
        (self.logs_dir / "agent.stderr").write_text(result.stderr or "")
        if result.return_code:
            raise RuntimeError(f"DSWizard workflow failed ({result.return_code}): {result.stderr or result.stdout}")
        context.metadata = {"submission_dir": "/app/submission", "stages": ["exploration", "planning", "implementation"]}
