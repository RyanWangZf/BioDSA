"""Unified biological target search and information tools.

This module provides unified search and retrieval of biological targets,
integrating information from multiple authoritative databases including
Open Targets, KEGG, and Gene Ontology.
"""

from .unified_target_search import (
    search_targets_unified,
    fetch_target_details_unified
)

__all__ = [
    'search_targets_unified',
    'fetch_target_details_unified'
]

