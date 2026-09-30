from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


def load_riskcalcs(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict): raise ValueError("RiskCalcs must be an ID-to-calculator mapping")
    return [{"id": str(key), "name": value.get("title", "").strip(),
             "purpose": value.get("purpose", "").strip(), "specialty": value.get("specialty", "").strip(),
             "computation": value.get("computation", ""), "interpretation": value.get("interpretation", "")}
            for key, value in payload.items()]


def bm25_rank(query: str, calculators: list[dict], top_k: int = 10) -> list[dict]:
    """Dependency-free BM25 matching used by the legacy default retrieval path."""
    tokenize = lambda value: re.findall(r"\b[a-z0-9]+\b", value.lower())
    documents = [tokenize(" ".join(str(row.get(key, "")) for key in ("name", "purpose", "specialty"))) for row in calculators]
    if not documents: return []
    average = sum(map(len, documents)) / len(documents)
    document_frequency = Counter(term for tokens in documents for term in set(tokens))
    query_terms = tokenize(query)
    scored = []
    for row, tokens in zip(calculators, documents):
        frequencies = Counter(tokens); score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency: continue
            inverse = math.log((len(documents) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5) + 1)
            score += inverse * frequency * 2.5 / (frequency + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / average))
        if score: scored.append({**row, "retrieval_score": score})
    return sorted(scored, key=lambda row: row["retrieval_score"], reverse=True)[:top_k]
