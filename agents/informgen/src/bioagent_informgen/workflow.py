from __future__ import annotations

from pathlib import Path
from .client import ModelClient
from . import prompts


class InformGenAgent:
    def __init__(self, config: dict, workspace: Path):
        system = config.setdefault("system_prompts", {})
        system["assemble_document"] = prompts.DOCUMENT_ASSEMBLY_PROMPT
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def _call(self, stage, payload):
        if stage.startswith("draft:") or stage.startswith("revise:"):
            self.config["system_prompts"].setdefault(stage, prompts.SECTION_WRITER_SYSTEM_PROMPT)
        elif stage.startswith("review:"):
            self.config["system_prompts"].setdefault(stage, prompts.SECTION_REVIEWER_SYSTEM_PROMPT)
        value = self.client.complete(stage, payload)
        self.trajectory.append({"event": stage, "section": payload.get("section"), "output": value})
        return value

    def run(self, item: dict) -> dict:
        source = item["source_document"]
        sections = item["template_sections"]
        completed, drafts, reviews = {}, {}, {}
        for section in sections:
            name = section["name"]
            draft = self._call(f"draft:{name}", {"section": name, "requirements": section, "source": source})
            drafts[name] = [draft]
            for revision in range(int(self.config.get("max_revisions", 2)) + 1):
                review = self._call(f"review:{name}", {"section": name, "draft": draft, "requirements": section})
                reviews.setdefault(name, []).append(review)
                if review.get("complete"):
                    self.trajectory.append({"event": "section_complete", "section": name, "revision": revision})
                    break
                if revision >= int(self.config.get("max_revisions", 2)):
                    raise RuntimeError(f"section {name} did not pass review")
                draft = self._call(f"revise:{name}", {"section": name, "draft": draft, "review": review, "source": source})
                drafts[name].append(draft)
            completed[name] = draft
        final = self._call("assemble_document", {"sections": completed, "template": sections})
        return {"final_answer": final, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls)},
                "artifacts": {"section_drafts.json": drafts, "section_reviews.json": reviews, "final_document.md": final}}
