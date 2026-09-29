from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import override

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class DeepEvidenceOptions(AgentOptions):
    provider: str = "mock"
    endpoint: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    tool_mode: str = "stub"
    knowledge_bases: list[str] = ["pubmed_papers", "clinical_trials"]
    routes: list[str] = ["bfs", "dfs"]
    main_search_rounds_budget: int = 2
    main_action_rounds_budget: int = 6
    subagent_action_rounds_budget: int = 3
    tool_call_budget: int = 6
    tool_timeout_seconds: float = 10
    timeout_seconds: float = 90
    max_tokens: int = 2000
    max_attempts: int = 2
    reasoning_effort: str | None = None
    code_execution: bool = True
    item_ids: list[str] = []
    item_timeout_seconds: float = 300


class DeepEvidenceHarborAgent(BaseAgent):
    options_model = DeepEvidenceOptions

    @staticmethod
    @override
    def name() -> str:
        return "bioagent-deepevidence"

    @override
    def version(self) -> str:
        return "0.2.0"

    @override
    async def setup(self, environment: BaseEnvironment) -> None:
        stage = self.logs_dir / "package-stage"
        if stage.exists():
            shutil.rmtree(stage)
        shutil.copytree(Path(__file__).resolve().parent, stage / "bioagent_deepevidence")
        await environment.upload_dir(stage, "/tmp/bioagent-deepevidence")
        result = await environment.exec("python3 -c \"import shutil,site; shutil.copytree('/tmp/bioagent-deepevidence/bioagent_deepevidence', site.getsitepackages()[0]+'/bioagent_deepevidence', dirs_exist_ok=True)\"", user="root", timeout_sec=180)
        if result.return_code:
            raise RuntimeError(f"DeepEvidence install failed: {result.stderr or result.stdout}")

    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        request = self.logs_dir / "harbor-input.json"
        config = self.options.model_dump()
        config["model"] = self.model_name
        config["execution_environment"] = {"backend": "local_subprocess", "timeout_seconds": config.pop("timeout_seconds")}
        config["code_execution"] = {"enabled": config["code_execution"]}
        config["memory"] = {"mode": "task"}
        item_ids = config.pop("item_ids")
        item_timeout_seconds = config.pop("item_timeout_seconds")
        request.write_text(json.dumps({"instruction": instruction, "config": config, "item_ids": item_ids, "item_timeout_seconds": item_timeout_seconds}))
        await environment.upload_file(request, "/tmp/bioagent-input.json")
        result = await environment.exec("python3 -m bioagent_deepevidence.harbor_runner /tmp/bioagent-input.json", cwd="/app")
        (self.logs_dir / "agent.stdout").write_text(result.stdout or "")
        (self.logs_dir / "agent.stderr").write_text(result.stderr or "")
        if result.return_code:
            raise RuntimeError(f"DeepEvidence workflow failed ({result.return_code}): {result.stderr or result.stdout}")
        usage_path = self.logs_dir / "usage.json"
        try:
            await environment.download_file("/app/submission/predictions.jsonl", usage_path)
            context.metadata = {"submission_dir": "/app/submission", "batch": True}
        except Exception:
            context.metadata = {"submission_dir": "/app/submission"}
