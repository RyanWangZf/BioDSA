from __future__ import annotations
import json
from pathlib import Path
from typing import override
from bioagent_harbor_runtime import install_command, stage_agent
from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

class DeepRareOptions(AgentOptions):
    provider: str="gateway"
    workflow_config: dict={}
    item_timeout_seconds: float=300
    item_ids: list[str]|None=None

class DeepRareHarborAgent(BaseAgent):
    options_model=DeepRareOptions
    @staticmethod
    @override
    def name()->str:return "bioagent-deeprare"
    @override
    def version(self)->str:return "0.1.0"
    @override
    async def setup(self,environment:BaseEnvironment)->None:
        stage=self.logs_dir/"package-stage"; stage_agent(Path(__file__).resolve().parent,"bioagent-deeprare","bioagent_deeprare",stage)
        await environment.upload_dir(stage,"/tmp/bioagent-deeprare")
        result=await environment.exec(install_command("/tmp/bioagent-deeprare","/opt/bioagent-deeprare","bioagent_deeprare"),user="root",timeout_sec=180)
        if result.return_code: raise RuntimeError(result.stderr or result.stdout)
    @override
    async def run(self,instruction:str,environment:BaseEnvironment,context:AgentContext)->None:
        payload={"instruction":instruction,"config":{**self.options.workflow_config,"provider":self.options.provider,"model":self.model_name},"item_timeout_seconds":self.options.item_timeout_seconds}
        if self.options.item_ids is not None: payload["item_ids"]=self.options.item_ids
        request=self.logs_dir/"harbor-input.json";request.write_text(json.dumps(payload));await environment.upload_file(request,"/tmp/bioagent-input.json")
        result=await environment.exec("/opt/bioagent-deeprare/bin/python -m bioagent_deeprare.harbor_runner /tmp/bioagent-input.json",cwd="/app")
        (self.logs_dir/"agent.stdout").write_text(result.stdout or "");(self.logs_dir/"agent.stderr").write_text(result.stderr or "")
        if result.return_code: raise RuntimeError(result.stderr or result.stdout)
        context.metadata={"submission_dir":"/app/submission","batch":True}
