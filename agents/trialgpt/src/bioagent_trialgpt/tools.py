from __future__ import annotations

import json
import urllib.parse
import urllib.request


class ClinicalTrialsClient:
    """ClinicalTrials.gov v2 retrieval used by the legacy search/details tools."""

    base = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, timeout_seconds: float = 15): self.timeout = timeout_seconds

    def search(self, terms: list[str], page_size: int = 20) -> list[dict]:
        query = urllib.parse.urlencode({"query.cond": " ".join(terms), "pageSize": page_size, "format": "json"})
        with urllib.request.urlopen(f"{self.base}?{query}", timeout=self.timeout) as response:
            payload = json.loads(response.read())
        rows = []
        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            identity = protocol.get("identificationModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            conditions = protocol.get("conditionsModule", {}).get("conditions", [])
            rows.append({"nct_id": identity.get("nctId"), "title": identity.get("briefTitle", ""),
                         "condition": ", ".join(conditions), "eligibility": eligibility.get("eligibilityCriteria", ""),
                         "minimum_age": eligibility.get("minimumAge"), "maximum_age": eligibility.get("maximumAge"),
                         "raw": study})
        return rows
