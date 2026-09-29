"""Unified pathway search and retrieval across multiple APIs.

This module aggregates pathway information from:
- KEGG Pathways
- Gene Ontology Biological Processes
"""

from .unified import search_pathways_unified, fetch_pathway_details_unified

__all__ = [
    'search_pathways_unified',
    'fetch_pathway_details_unified'
]

