from __future__ import annotations

import json
import urllib.parse
import urllib.request


def _json_request(url: str, payload: dict | None = None, timeout: float = 15):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    with urllib.request.urlopen(urllib.request.Request(url, data, headers), timeout=timeout) as response:
        return json.loads(response.read())


class GeneDatabaseTools:
    """Live g:Profiler, STRING, and NCBI contracts required by GeneAgent."""

    def __init__(self, timeout_seconds: float = 15): self.timeout = timeout_seconds

    def enrichment(self, genes: list[str]):
        return _json_request("https://biit.cs.ut.ee/gprofiler/api/gost/profile/",
                             {"organism": "hsapiens", "query": genes}, self.timeout)

    def interactions(self, genes: list[str]):
        params = urllib.parse.urlencode({"identifiers": "\r".join(genes), "species": 9606})
        return _json_request(f"https://string-db.org/api/json/network?{params}", timeout=self.timeout)

    def pubmed(self, term: str, limit: int = 5):
        params = urllib.parse.urlencode({"db": "pubmed", "term": term, "retmode": "json", "retmax": limit})
        return _json_request(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}", timeout=self.timeout)

    def collect(self, genes: list[str]):
        return {"enrichment": self.enrichment(genes), "interactions": self.interactions(genes),
                "pubmed": self.pubmed(" OR ".join(genes))}
