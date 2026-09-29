from __future__ import annotations

from typing import override

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class FixtureHarborAgent(BaseAgent):
    @staticmethod
    @override
    def name() -> str:
        return "bioagent-fixture"

    @override
    def version(self) -> str:
        return "0.2.0"

    @override
    async def setup(self, environment: BaseEnvironment) -> None:
        return

    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        if "offline network probe" in instruction.lower():
            command = "mkdir -p /app/submission && python3 -c \"import urllib.request; from pathlib import Path; p=Path('/app/submission/network.txt');\ntry: urllib.request.urlopen('https://example.com', timeout=3); p.write_text('reachable')\nexcept Exception: p.write_text('blocked')\""
        else:
            command = "mkdir -p /app/submission && printf 'fixture completed\\n' > /app/submission/final_answer.md && printf '{\"status\":\"ok\"}\\n' > /app/submission/artifact.json"
        result = await environment.exec(command, cwd="/app")
        if result.return_code:
            raise RuntimeError(result.stderr or result.stdout or "fixture failed")
        context.metadata = {"deterministic": True}
