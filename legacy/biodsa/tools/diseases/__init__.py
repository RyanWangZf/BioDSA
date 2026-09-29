"""Unified disease search and information tools.

This module provides unified access to multiple disease databases including
BioThings (MyDisease.info) and KEGG Disease Database.
"""

from .unified_disease_search import (
    search_diseases_unified,
    fetch_disease_details_unified,
    aggregate_disease_names,
    aggregate_disease_identifiers,
)

__all__ = [
    'search_diseases_unified',
    'fetch_disease_details_unified',
    'aggregate_disease_names',
    'aggregate_disease_identifiers',
]

