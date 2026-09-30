"""DeepRare's bounded nine-stage diagnostic workflow."""
from __future__ import annotations

import json
from .contract import json_object, public_case, sanitize
from .reasoning import attach_evidence, check_candidates, check_similar_cases, final_reflection, fuse_candidates, retry_if_all_rejected, zero_shot_diagnosis
from .retrieval import candidate_evidence, initial_retrieval
from .runtime import ModelSession, SourceSession, fixture_callers


class DeepRareAgent:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.trace: list[dict] = []

    def run(self, value: object) -> dict:
        case = public_case(value)
        model_caller = source_caller = None
        if self.config.get("provider", "fixture") == "fixture":
            model_caller, source_caller = fixture_callers(self.config)
        sources = SourceSession(self.config, source_caller, self.trace)
        models = ModelSession(self.config, model_caller, self.trace)
        retrieval = initial_retrieval(case, sources)
        zero_shot = zero_shot_diagnosis(case, models)
        similar_checks = check_similar_cases(case, retrieval["similar_cases"], models)
        candidates = fuse_candidates(case, retrieval, zero_shot, similar_checks, models)
        if not candidates:
            raise RuntimeError("no diagnosis identifier was returned by retrieval or model")
        evidence = candidate_evidence(candidates, sources)
        judgements = check_candidates(case, candidates, evidence, similar_checks, models)
        candidates, extra, judgements = retry_if_all_rejected(case, candidates, judgements, retrieval, sources, models)
        evidence.update(extra)
        grounded = attach_evidence(candidates, evidence, judgements)
        reflected = final_reflection(case, grounded, similar_checks, models)
        parsed = json_object(reflected, "diagnoses")
        ranked = sanitize(parsed.get("diagnoses", []) if parsed else grounded, sources.records, grounded)
        if not ranked:
            ranked = sanitize(grounded, sources.records, grounded)
        if not ranked:
            raise RuntimeError("could not construct a contract-valid diagnosis list")
        payload = {"diagnoses": ranked}
        return {"final_answer": "<RARE_DISEASE_FINAL>\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n</RARE_DISEASE_FINAL>\n",
                "diagnoses": ranked, "retrieval": retrieval, "similar_checks": similar_checks,
                "evidence": evidence, "judgements": judgements, "trace": self.trace,
                "usage": {"model_calls": models.calls, "source_calls": sources.calls}}
