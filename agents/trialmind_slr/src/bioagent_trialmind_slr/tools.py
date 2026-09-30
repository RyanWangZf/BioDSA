from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class PubMedClient:
    """The legacy PubMed search + abstract-fetch contract using NCBI E-utilities."""

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, timeout_seconds: float = 15, email: str = "slr_agent@example.com"):
        self.timeout, self.email = timeout_seconds, email

    def _get(self, endpoint: str, **params) -> bytes:
        params.update({"tool": "bioagent_gym_trialmind", "email": self.email})
        url = f"{self.base}/{endpoint}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            return response.read()

    def search(self, query: str, max_results: int = 20) -> list[dict]:
        payload = json.loads(self._get("esearch.fcgi", db="pubmed", term=query,
                                      retmode="json", retmax=max_results))
        pmids = payload["esearchresult"]["idlist"]
        if not pmids:
            return []
        root = ET.fromstring(self._get("efetch.fcgi", db="pubmed", id=",".join(pmids), retmode="xml"))
        rows = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID", default="")
            title = "".join(article.find(".//ArticleTitle").itertext()) if article.find(".//ArticleTitle") is not None else ""
            abstract = " ".join("".join(node.itertext()) for node in article.findall(".//AbstractText"))
            rows.append({"pmid": pmid, "title": title, "abstract": abstract, "search_text": f"{title} {abstract}"})
        return rows
