from __future__ import annotations

import json
import urllib.parse
import urllib.request


def pubmed_search(query: str, max_results: int = 5, timeout_seconds: float = 15) -> list[dict]:
    """Small live PubMed boundary matching the legacy VirtualLab search tool."""
    params = urllib.parse.urlencode({"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results})
    with urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + params,
                               timeout=timeout_seconds) as response:
        ids = json.loads(response.read())["esearchresult"]["idlist"]
    if not ids: return []
    summary = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    with urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + summary,
                               timeout=timeout_seconds) as response:
        payload = json.loads(response.read())["result"]
    return [{"pmid": pmid, "title": payload[pmid].get("title", "")} for pmid in ids]
