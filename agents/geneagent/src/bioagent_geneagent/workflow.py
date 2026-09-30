from __future__ import annotations

from pathlib import Path
from .client import ModelClient
from . import prompts
from .tools import GeneDatabaseTools


class GeneAgent:
    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {}).update({
            "initial_gene_set_analysis": prompts.BASELINE_SYSTEM_PROMPT,
            "topic_claims": prompts.TOPIC_CLAIM_GENERATION_PROMPT,
            "verify_claim": prompts.VERIFICATION_WORKER_SYSTEM_PROMPT,
            "topic_update": prompts.TOPIC_MODIFICATION_PROMPT,
            "analysis_claims": prompts.ANALYSIS_CLAIM_GENERATION_PROMPT,
            "analysis_update": prompts.ANALYSIS_SUMMARIZATION_PROMPT,
        })
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def _call(self, stage, payload):
        value = self.client.complete(stage, payload)
        self.trajectory.append({"event": stage, "input": payload, "output": value})
        return value

    def _verify(self, claim, evidence):
        return self._call("verify_claim", {"claim": claim, "evidence": evidence})

    def run(self, item: dict) -> dict:
        genes = item.get("genes") or item["instruction"]
        evidence = item.get("tool_fixture")
        if evidence is None:
            evidence = GeneDatabaseTools(float(self.config.get("tool_timeout_seconds", 15))).collect(genes)
        baseline = self._call("initial_gene_set_analysis", {"genes": genes, "tools": evidence})
        topic_claims = self._call("topic_claims", {"genes": genes, "baseline": baseline})
        topic_reports = [{"claim": claim, "verification": self._verify(claim, evidence)} for claim in topic_claims]
        topic = self._call("topic_update", {"baseline": baseline, "verification_reports": topic_reports})
        analysis_claims = self._call("analysis_claims", {"genes": genes, "topic": topic})
        analysis_reports = [{"claim": claim, "verification": self._verify(claim, evidence)} for claim in analysis_claims]
        final = self._call("analysis_update", {"topic": topic, "verification_reports": analysis_reports})
        return {"final_answer": final, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls), "tool_calls": len(topic_claims)+len(analysis_claims)},
                "artifacts": {"topic_verification.json": topic_reports, "analysis_verification.json": analysis_reports,
                              "gene_analysis.json": {"baseline": baseline, "updated_topic": topic, "final": final}}}
