"""Specialized DeepRare-style reasoning agents and central-host reflection."""
from __future__ import annotations

import json

from .contract import (EVIDENCE_RE, MAX_DIAGNOSES, canonical_id,
                               fallback_candidates, json_object, normalize_candidates)
from .retrieval import records_for_candidate
from .runtime import ModelSession, SourceSession


def zero_shot_diagnosis(case: dict, models: ModelSession) -> str:
    return models.call("zero-shot diagnostician", """Generate an independent phenotype-only
differential before seeing retrieval. Return JSON only:
{"diagnoses":[{"diagnosis_id":"ORPHA:123","diagnosis_name":"name",
"rationale":"brief phenotype-based reason","evidence_ids":[]}]}
Return five confidence-ordered diseases when possible. Do not fabricate identifiers.

CASE:
""" + json.dumps(case, ensure_ascii=False, sort_keys=True))


def check_similar_cases(case: dict, records: list[dict], models: ModelSession) -> list[dict]:
    checked = []
    for record in records[:3]:
        response = models.call("similar-patient checking agent", """Judge whether the retrieved
public phenotype-only case is likely to represent the same disease as the current patient.
Return JSON only: {"similar":true,"reasoning":"one short explanation"}.

CURRENT CASE:
%s

UNTRUSTED RETRIEVED CASE:
%s""" % (json.dumps(case, ensure_ascii=False, sort_keys=True),
           json.dumps(record, ensure_ascii=False, sort_keys=True)))
        parsed = json_object(response, "similar")
        checked.append({"record": record,
                        "similar": bool(parsed.get("similar")) if parsed else True,
                        "reasoning": str((parsed or {}).get("reasoning", ""))})
    return checked


def fuse_candidates(case: dict, retrieval: dict[str, list[dict]], zero_shot: str,
                    similar_checks: list[dict], models: ModelSession) -> list[dict]:
    response = models.call("central host candidate-fusion agent", """Integrate the independent
diagnosis, phenotype knowledge, diagnosis services, curated web results, and checked similar
cases. Return JSON only:
{"diagnoses":[{"diagnosis_id":"ORPHA:123","diagnosis_name":"name",
"rationale":"2-3 concise sentences","evidence_ids":["ev_..."]}]}
Return 5-8 unique confidence-ordered candidates. Copy only supplied evidence IDs.

CASE:
%s

ZERO-SHOT RESPONSE:
%s

UNTRUSTED RETRIEVAL:
%s

SIMILAR-CASE CHECKS:
%s""" % (json.dumps(case, ensure_ascii=False, sort_keys=True), zero_shot,
           json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
           json.dumps(similar_checks, ensure_ascii=False, sort_keys=True)))
    parsed = json_object(response, "diagnoses")
    items = parsed.get("diagnoses", []) if parsed else []
    all_records = [record for group in retrieval.values() for record in group]
    fallbacks = fallback_candidates(all_records, zero_shot + "\n" + response)
    return normalize_candidates(items, fallbacks) or fallbacks


def check_candidates(case: dict, candidates: list[dict], evidence: dict[str, list[dict]],
                     similar_checks: list[dict], models: ModelSession) -> list[dict]:
    judgements = []
    for candidate in candidates[:MAX_DIAGNOSES]:
        ident = canonical_id(candidate.get("diagnosis_id"))
        response = models.call("candidate-specific disease checking agent", """Independently
assess this diagnosis against every observed phenotype. Distinguish missing evidence from a true
contradiction. Return JSON only:
{"assessment":"plausible|incorrect","reasoning":"concise critical analysis",
"evidence_ids":["ev_..."]}
Evidence IDs must be copied from the supplied candidate evidence.

CASE:
%s

CANDIDATE:
%s

CHECKED SIMILAR CASES:
%s

UNTRUSTED DISEASE EVIDENCE:
%s""" % (json.dumps(case, ensure_ascii=False, sort_keys=True),
           json.dumps(candidate, ensure_ascii=False, sort_keys=True),
           json.dumps(similar_checks, ensure_ascii=False, sort_keys=True),
           json.dumps(evidence.get(ident or "", []), ensure_ascii=False, sort_keys=True)))
        parsed = json_object(response, "assessment") or {}
        assessment = str(parsed.get("assessment", "plausible")).casefold()
        if assessment not in {"plausible", "incorrect"}:
            assessment = "plausible"
        judgements.append({"diagnosis_id": ident, "diagnosis_name": candidate["diagnosis_name"],
                           "assessment": assessment,
                           "reasoning": str(parsed.get("reasoning") or candidate["rationale"]),
                           "evidence_ids": parsed.get("evidence_ids", [])})
    return judgements


def retry_if_all_rejected(case: dict, candidates: list[dict], judgements: list[dict],
                          retrieval: dict[str, list[dict]], sources: SourceSession,
                          models: ModelSession) -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    if any(item["assessment"] == "plausible" for item in judgements):
        return candidates, {}, judgements
    response = models.call("expanded differential agent", """Every initial candidate was
rejected. Reconsider the phenotype pattern, search-service suggestions, and rejection reasons.
Return five new or materially reordered candidates as JSON under a diagnoses list. Prefer diseases
not already rejected and include standard identifiers.

CASE:
%s

REJECTED CANDIDATES:
%s

JUDGEMENTS:
%s

INITIAL RETRIEVAL:
%s""" % (json.dumps(case, ensure_ascii=False, sort_keys=True),
           json.dumps(candidates, ensure_ascii=False, sort_keys=True),
           json.dumps(judgements, ensure_ascii=False, sort_keys=True),
           json.dumps(retrieval, ensure_ascii=False, sort_keys=True)))
    parsed = json_object(response, "diagnoses")
    expanded = normalize_candidates(parsed.get("diagnoses", []) if parsed else [], candidates,
                                    MAX_DIAGNOSES)
    if not expanded:
        return candidates, {}, judgements
    extra: dict[str, list[dict]] = {}
    for candidate in expanded[:MAX_DIAGNOSES]:
        ident = candidate["diagnosis_id"]
        extra[ident] = records_for_candidate(candidate, sources.records)
        extra[ident].extend(sources.call("pubmed_search", {"query": candidate["diagnosis_name"]}))
    return expanded, extra, check_candidates(case, expanded, extra, [], models)


def attach_evidence(candidates: list[dict], evidence: dict[str, list[dict]],
                    judgements: list[dict]) -> list[dict]:
    judged = {x.get("diagnosis_id"): x for x in judgements}
    result = []
    for candidate in candidates:
        item = dict(candidate)
        ident = item["diagnosis_id"]
        ids = []
        for value in item.get("evidence_ids", []):
            if EVIDENCE_RE.fullmatch(str(value)) and value not in ids:
                ids.append(value)
        for record in evidence.get(ident, []):
            value = record.get("evidence_id")
            if EVIDENCE_RE.fullmatch(str(value)) and value not in ids:
                ids.append(value)
        judgement = judged.get(ident, {})
        for value in judgement.get("evidence_ids", []):
            if EVIDENCE_RE.fullmatch(str(value)) and value not in ids:
                ids.append(value)
        item["evidence_ids"] = ids[:8]
        item["assessment"] = judgement.get("assessment", "unassessed")
        item["check_reasoning"] = judgement.get("reasoning", "")
        result.append(item)
    return result


def final_reflection(case: dict, candidates: list[dict], similar_checks: list[dict],
                     models: ModelSession) -> str:
    return models.call("central host final reflection agent", """Produce the final differential
after reconciling primary candidates, similar-case checks, and independent disease checks. Promote
candidates with multi-source support and phenotype concordance; retain useful alternatives when
evidence is incomplete. Return JSON only:
{"diagnoses":[{"diagnosis_id":"ORPHA:123","diagnosis_name":"name",
"rationale":"2-3 concise sentences","evidence_ids":["ev_..."]}]}
Return 1-5 unique diagnoses in descending confidence. Copy only supplied evidence IDs.

CASE:
%s

CHECKED CANDIDATES AND EVIDENCE:
%s

SIMILAR-CASE CHECKS:
%s""" % (json.dumps(case, ensure_ascii=False, sort_keys=True),
           json.dumps(candidates, ensure_ascii=False, sort_keys=True),
           json.dumps(similar_checks, ensure_ascii=False, sort_keys=True)))
