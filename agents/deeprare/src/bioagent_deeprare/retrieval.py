"""DeepRare-style phenotype, similar-case, web, and disease knowledge retrieval."""
from __future__ import annotations

import json

from .contract import MAX_DIAGNOSES, canonical_id
from .runtime import SourceSession


def phenotype_query(case: dict) -> str:
    terms = [str(x).strip() for x in case["phenotype_terms"] if str(x).strip()]
    return ((" ".join(terms[:12]) + " rare disease diagnosis")[:900]
            or "rare disease phenotype diagnosis")


def initial_retrieval(case: dict, sources: SourceSession) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {"hpo": [], "similar_cases": [], "predictions": [], "web": []}
    for hpo_id in case["phenotype_hpo_ids"][:4]:
        groups["hpo"].extend(sources.call("hpo_lookup", {"hpo_id": hpo_id}))
    hpos = case["phenotype_hpo_ids"][:100]
    if hpos:
        groups["similar_cases"] = sources.call("fit_case_search", {"hpo_ids": hpos})
        groups["predictions"].extend(sources.call("phenobrain_predict", {"hpo_ids": hpos}))
        groups["predictions"].extend(sources.call("pubcasefinder_predict", {"hpo_ids": hpos}))
    query = phenotype_query(case)
    for tool in ("medlineplus_search", "wikipedia_search", "pubmed_search"):
        groups["web"].extend(sources.call(tool, {"query": query}))
    return groups


def records_for_candidate(candidate: dict, records: list[dict]) -> list[dict]:
    ident = canonical_id(candidate.get("diagnosis_id"))
    name = str(candidate.get("diagnosis_name", "")).casefold()
    matched = []
    for record in records:
        identifier_blob = json.dumps(record.get("identifiers", {}), ensure_ascii=False)
        title = str(record.get("title", ""))
        if (ident and canonical_id(identifier_blob) == ident) or (name and name in title.casefold()):
            matched.append(record)
    return matched


def candidate_evidence(candidates: list[dict], sources: SourceSession) -> dict[str, list[dict]]:
    evidence: dict[str, list[dict]] = {}
    initial = list(sources.records)
    for item in candidates[:MAX_DIAGNOSES]:
        ident = canonical_id(item.get("diagnosis_id"))
        if not ident:
            continue
        batch = records_for_candidate(item, initial)
        if ident.startswith("ORPHA:"):
            batch.extend(sources.call("orphanet_lookup", {"disease_id": ident}))
        name = str(item.get("diagnosis_name") or ident).strip()
        batch.extend(sources.call("pubmed_search", {"query": name}))
        batch.extend(sources.call("crossref_search", {"query": name + " rare disease"}))
        evidence[ident] = batch
    return evidence
