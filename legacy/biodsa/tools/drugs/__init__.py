"""Unified drug search and information retrieval from multiple sources.

This module provides unified access to drug information from:
- BioThings (MyChem.info) - drug properties, identifiers, pharmacology
- OpenFDA - FDA approval data and product labeling
- KEGG - drug/compound information and pathways
"""

__all__ = [
    "search_drugs_unified",
    "fetch_drug_details_unified",
    "aggregate_drug_names",
    "aggregate_drug_identifiers",
]

from .unified_drug_search import (
    search_drugs_unified,
    fetch_drug_details_unified,
    aggregate_drug_names,
    aggregate_drug_identifiers,
)

