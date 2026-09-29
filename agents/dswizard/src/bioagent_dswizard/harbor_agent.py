from __future__ import annotations

import json
import shutil
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
        if stage.exists():
            shutil.rmtree(stage)
        shutil.copytree(Path(__file__).resolve().parent, stage / "bioagent_dswizard")
        await environment.upload_dir(stage, "/tmp/bioagent-dswizard")
        result = await environment.exec("python3 -c \"import shutil,site; shutil.copytree('/tmp/bioagent-dswizard/bioagent_dswizard', site.getsitepackages()[0]+'/bioagent_dswizard', dirs_exist_ok=True)\"", user="root", timeout_sec=180)
        if result.return_code:
            raise RuntimeError(f"DSWizard install failed: {result.stderr or result.stdout}")

    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        request = self.logs_dir / "harbor-input.json"
        config = self.options.model_dump()
        config.update({"model": self.model_name, "execution_environment": {"backend": "local_subprocess", "timeout_seconds": config.pop("timeout_seconds")}})
        request.write_text(json.dumps({"instruction": instruction, "config": config}))
        await environment.upload_file(request, "/tmp/bioagent-input.json")
        result = await environment.exec("python3 -m bioagent_dswizard.harbor_runner /tmp/bioagent-input.json", cwd="/app")
        (self.logs_dir / "agent.stdout").write_text(result.stdout or "")
        (self.logs_dir / "agent.stderr").write_text(result.stderr or "")
        if result.return_code:
            raise RuntimeError(f"DSWizard workflow failed ({result.return_code}): {result.stderr or result.stdout}")
        context.metadata = {"submission_dir": "/app/submission", "stages": ["exploration", "planning", "implementation"]}
