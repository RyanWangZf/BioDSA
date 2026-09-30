"""Input, identifier, JSON, and final-output contracts for the reference agent."""
from __future__ import annotations

from collections.abc import Iterable
import json
import re

PUBLIC_FIELDS = {"schema", "case_id", "dataset", "phenotype_hpo_ids", "phenotype_terms"}
ID_RE = re.compile(r"(?i)\b(OMIM|ORPHA)\s*:?\s*(\d+)\b|\b(CCRD:[^\s,;\]\[}\{]+)")
EVIDENCE_RE = re.compile(r"^ev_[0-9a-f]{24}$")
MAX_DIAGNOSES = 5


def public_case(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("case must be an object")
    case = {key: value[key] for key in PUBLIC_FIELDS if key in value}
    if (set(case) != PUBLIC_FIELDS or case["schema"] != "rare-disease-diagnosis-case/v1" or
            not isinstance(case["case_id"], str) or not isinstance(case["dataset"], str) or
            not isinstance(case["phenotype_hpo_ids"], list) or
            not isinstance(case["phenotype_terms"], list)):
        raise ValueError("invalid case")
    return case


def canonical_id(value: object) -> str | None:
    match = ID_RE.search(str(value or ""))
    if not match:
        return None
    if match.group(3):
        return "CCRD:" + match.group(3).split(":", 1)[1].rstrip(".:")
    return f"{match.group(1).upper()}:{match.group(2)}"


def json_object(text: str, key: str) -> dict | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and key in value:
            return value
    return None


def fallback_candidates(records: Iterable[dict], text: str = "") -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    for record in records:
        identifiers = record.get("identifiers", {})
        blobs = list(identifiers.values()) if isinstance(identifiers, dict) else []
        blobs.extend([record.get("title", ""), record.get("snippet", "")])
        for blob in blobs:
            ident = canonical_id(blob)
            if ident and ident not in seen:
                seen.add(ident)
                evidence_id = str(record.get("evidence_id", ""))
                result.append({"diagnosis_id": ident,
                               "diagnosis_name": str(record.get("title") or ident),
                               "rationale": "Phenotype retrieval ranked this disease.",
                               "evidence_ids": [evidence_id]
                               if EVIDENCE_RE.fullmatch(evidence_id) else []})
    for match in ID_RE.finditer(text):
        ident = canonical_id(match.group(0))
        if ident and ident not in seen:
            seen.add(ident)
            result.append({"diagnosis_id": ident, "diagnosis_name": ident,
                           "rationale": "Selected by phenotype-based differential diagnosis.",
                           "evidence_ids": []})
    return result[:8]


def normalize_candidates(items: Iterable[object], fallback: list[dict] | None = None,
                         limit: int = 8) -> list[dict]:
    bases = {canonical_id(x.get("diagnosis_id")): x for x in (fallback or [])}
    result: list[dict] = []
    seen: set[str] = set()
    for raw in items:
        if not isinstance(raw, dict):
            continue
        ident = canonical_id(raw.get("diagnosis_id"))
        if not ident or ident in seen:
            continue
        base = bases.get(ident, {})
        result.append({"diagnosis_id": ident,
                       "diagnosis_name": str(raw.get("diagnosis_name") or
                                             base.get("diagnosis_name") or ident).strip(),
                       "rationale": str(raw.get("rationale") or base.get("rationale") or
                                        "Phenotypes support this differential.").strip(),
                       "evidence_ids": raw.get("evidence_ids", base.get("evidence_ids", []))})
        seen.add(ident)
        if len(result) == limit:
            break
    return result


def sanitize(items: Iterable[object], records: list[dict], fallback: list[dict]) -> list[dict]:
    valid_evidence = {str(record.get("evidence_id")) for record in records
                      if EVIDENCE_RE.fullmatch(str(record.get("evidence_id", "")))}
    fallback_by_id = {canonical_id(x.get("diagnosis_id")): x for x in fallback}
    result: list[dict] = []
    seen: set[str] = set()
    for raw in items:
        if not isinstance(raw, dict):
            continue
        ident = canonical_id(raw.get("diagnosis_id"))
        if not ident or ident in seen:
            continue
        base = fallback_by_id.get(ident, {})
        name = str(raw.get("diagnosis_name") or base.get("diagnosis_name") or ident).strip()
        rationale = str(raw.get("rationale") or base.get("rationale") or
                        "Phenotype pattern supports this differential diagnosis.").strip()
        requested = raw.get("evidence_ids", base.get("evidence_ids", []))
        cited = []
        if isinstance(requested, list):
            for evidence_id in requested:
                if evidence_id in valid_evidence and evidence_id not in cited:
                    cited.append(evidence_id)
        result.append({"diagnosis_id": ident, "diagnosis_name": name,
                       "rationale": rationale, "evidence_ids": cited[:8]})
        seen.add(ident)
        if len(result) == MAX_DIAGNOSES:
            break
    return result
