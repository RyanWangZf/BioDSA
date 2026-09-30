from __future__ import annotations
import json
from pathlib import Path
from typing import override
from bioagent_harbor_runtime import install_command, stage_agent
from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

class Options(AgentOptions):
    split: str = "fit"
    item_ids_by_dataset: dict[str,list[str]]
    item_timeout_seconds: float = 30

class BDRFixtureAgent(BaseAgent):
    options_model=Options
    @staticmethod
    @override
    def name()->str:return "bioagent-bdr-fixture"
    @override
    def version(self)->str:return "0.2.0"
    @override
    async def setup(self,environment:BaseEnvironment)->None:
        stage=self.logs_dir/"package-stage";stage_agent(Path(__file__).resolve().parent,"bioagent-fixture","bioagent_fixture",stage);await environment.upload_dir(stage,"/tmp/bioagent-fixture")
        result=await environment.exec(install_command("/tmp/bioagent-fixture","/opt/bioagent-fixture","bioagent_fixture"),user="root",timeout_sec=180)
        if result.return_code:raise RuntimeError(result.stderr or result.stdout)
    @override
    async def run(self,instruction:str,environment:BaseEnvironment,context:AgentContext)->None:
        request=self.logs_dir/"harbor-input.json";request.write_text(json.dumps({"instruction":instruction,"config":{},"split":self.options.split,"item_ids_by_dataset":self.options.item_ids_by_dataset,"item_timeout_seconds":self.options.item_timeout_seconds}));await environment.upload_file(request,"/tmp/bioagent-input.json")
        result=await environment.exec("/opt/bioagent-fixture/bin/python -m bioagent_fixture.bdr_runner /tmp/bioagent-input.json",cwd="/app")
        if result.return_code:raise RuntimeError(result.stderr or result.stdout)
        context.metadata={"submission_dir":"/app/submission","batch":True,"fixture":True}
