from __future__ import annotations

from pathlib import Path
from .client import ModelClient
from . import prompts
from .tools import PubMedClient


class TrialMindSLRAgent:
    """Four-stage SLR workflow preserving the legacy transition boundaries."""

    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {}).update({
            "search_queries": prompts.SEARCH_AGENT_SYSTEM_PROMPT,
            "eligibility_criteria": prompts.SCREENING_AGENT_SYSTEM_PROMPT,
            "screen_study": prompts.STUDY_SCREENING_PROMPT,
            "extraction_fields": prompts.EXTRACTION_AGENT_SYSTEM_PROMPT,
            "extract_study": prompts.DATA_EXTRACTION_PROMPT,
            "synthesize_evidence": prompts.EVIDENCE_SYNTHESIS_PROMPT,
            "generate_report": prompts.FINAL_REPORT_PROMPT,
        })
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def _event(self, event, **values):
        self.trajectory.append({"event": event, **values})

    def run(self, item: dict) -> dict:
        question = item["instruction"]
        self._event("search_start")
        queries = self.client.complete("search_queries", {"question": question})
        studies, calls = [], 0
        fixture = item.get("pubmed_fixture")
        pubmed = PubMedClient(float(self.config.get("tool_timeout_seconds", 15)), self.config.get("ncbi_email", "slr_agent@example.com"))
        for query in queries[: int(self.config.get("search_budget", 3))]:
            calls += 1
            found = ([x for x in fixture if query.lower() in x.get("search_text", "").lower()]
                     if fixture is not None else pubmed.search(query, int(self.config.get("max_results", 20))))
            studies.extend(found); self._event("pubmed_search", query=query, count=len(found))
        unique = {str(x["pmid"]): x for x in studies}
        self._event("search_finalized", identified=len(unique))

        criteria = self.client.complete("eligibility_criteria", {"question": question})
        screened = []
        self._event("screening_start", criteria=criteria)
        screening_rows = list(unique.values())
        screening_budget = int(self.config.get("screening_budget", len(screening_rows)))
        for study in screening_rows[:screening_budget]:
            prediction = self.client.complete("screen_study", {"study": study, "criteria": criteria})
            screened.append({"study": study, **prediction}); self._event("study_screened", pmid=study["pmid"], decision=prediction["decision"])
        included = [x for x in screened if x["decision"] == "include"]
        self._event("screening_finalized", included=len(included), excluded=len(screened)-len(included))

        fields = self.client.complete("extraction_fields", {"question": question})
        extracted = []
        self._event("extraction_start", fields=fields)
        extraction_budget = int(self.config.get("extraction_budget", len(included)))
        for row in included[:extraction_budget]:
            value = self.client.complete("extract_study", {"study": row["study"], "fields": fields})
            extracted.append({"pmid": row["study"]["pmid"], "fields": value}); self._event("study_extracted", pmid=row["study"]["pmid"])
        self._event("extraction_finalized", count=len(extracted))

        synthesis = self.client.complete("synthesize_evidence", {"question": question, "studies": extracted})
        report = self.client.complete("generate_report", {"question": question, "screened": screened, "synthesis": synthesis})
        self._event("synthesis_finalized", included=len(included))
        return {"final_answer": report, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls), "tool_calls": calls},
                "artifacts": {"screening.json": screened, "extraction.json": extracted,
                              "synthesis.json": synthesis, "prisma.json": {"identified": len(unique), "screened": len(screened), "included": len(included)}}}
