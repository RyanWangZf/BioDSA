from __future__ import annotations

from pathlib import Path
from .client import ModelClient
from . import prompts
from .tools import ClinicalTrialsClient


class TrialGPTAgent:
    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {}).update({
            "retrieval_query": prompts.RETRIEVAL_AGENT_SYSTEM_PROMPT,
            "eligibility_match": prompts.MATCHING_AGENT_SYSTEM_PROMPT,
            "rank_trials": prompts.RANKING_SYNTHESIS_PROMPT,
            "trial_summary": prompts.RANKING_SYNTHESIS_PROMPT,
        })
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def _event(self, event, **values): self.trajectory.append({"event": event, **values})

    def run(self, item: dict) -> dict:
        patient = item["patient"]
        query = self.client.complete("retrieval_query", {"patient": patient})
        self._event("retrieval_query", query=query)
        fixture = item.get("trial_fixture")
        candidates = ([trial for trial in fixture if
                       any(term.lower() in (trial.get("condition", "")+trial.get("title", "")).lower() for term in query.get("terms", []))]
                      if fixture is not None else ClinicalTrialsClient(float(self.config.get("tool_timeout_seconds", 15))).search(query.get("terms", []), int(self.config.get("max_results", 20))))
        self._event("clinical_trial_search", count=len(candidates))
        details = [{**trial, "details_loaded": True} for trial in candidates]
        self._event("trial_details", ids=[x["nct_id"] for x in details])
        matches = []
        for trial in details:
            decision = self.client.complete("eligibility_match", {"patient": patient, "trial": trial})
            matches.append({"trial": trial, **decision}); self._event("eligibility_match", nct_id=trial["nct_id"], eligible=decision["eligible"])
        ranked = self.client.complete("rank_trials", {"patient": patient, "matches": matches})
        self._event("ranking_complete", order=[x["nct_id"] for x in ranked])
        final = self.client.complete("trial_summary", {"patient": patient, "ranked": ranked, "matches": matches})
        return {"final_answer": final, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls), "tool_calls": 2 + len(matches)},
                "artifacts": {"trial_details.json": details, "eligibility.json": matches, "ranked_trials.json": ranked}}
