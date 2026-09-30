from __future__ import annotations

from pathlib import Path
from .client import ModelClient
from . import prompts
from .tools import pubmed_search


class VirtualLabAgent:
    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {}).update({
            "team_lead_synthesize": prompts.SYNTHESIS_PROMPT,
            "team_lead_final": prompts.SUMMARY_PROMPT,
            "individual_complete": prompts.SUMMARY_PROMPT,
            "assemble": prompts.MERGE_PROMPT,
        })
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def _call(self, stage, payload):
        answer = self.client.complete(stage, payload)
        self.trajectory.append({"event": stage, "speaker": payload.get("participant"), "content": answer})
        return answer

    def run(self, item: dict) -> dict:
        mode = item.get("mode", "team")
        if mode == "team":
            participants = item["participants"]
            lead = next(p for p in participants if p.get("role") == "leader")
            members = [p for p in participants if p is not lead]
            references = item.get("reference_fixture")
            if references is None and self.config.get("use_pubmed"):
                references = pubmed_search(item["instruction"], int(self.config.get("max_results", 5)), float(self.config.get("tool_timeout_seconds", 15)))
            context = [self._call("team_lead_initial", {"participant": lead["name"], "agenda": item["instruction"], "references": references or []})]
            for round_index in range(int(item.get("rounds", 1))):
                for member in members:
                    context.append(self._call("team_member_response", {"participant": member["name"], "round": round_index, "context": context}))
                context.append(self._call("team_lead_synthesize", {"participant": lead["name"], "round": round_index, "context": context}))
            final = self._call("team_lead_final", {"participant": lead["name"], "context": context})
        elif mode == "individual":
            draft = self._call("individual_agent", {"participant": item.get("agent", "scientist"), "agenda": item["instruction"]})
            for round_index in range(int(item.get("rounds", 1))):
                critique = self._call("individual_critic", {"participant": item.get("critic", "critic"), "draft": draft, "round": round_index})
                draft = self._call("individual_revise", {"participant": item.get("agent", "scientist"), "draft": draft, "critique": critique})
            final = self._call("individual_complete", {"participant": item.get("agent", "scientist"), "draft": draft})
        else:
            raise ValueError(f"unknown meeting mode: {mode}")
        return {"final_answer": final, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls)},
                "artifacts": {"meeting.json": {"mode": mode, "messages": self.trajectory}}}
