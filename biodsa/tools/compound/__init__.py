"""Unified compound search and retrieval across multiple APIs.

This module aggregates compound information from:
- KEGG Compound Database
- PubChem
"""

from .unified import search_compounds_unified, fetch_compound_details_unified

__all__ = [
    'search_compounds_unified',
    'fetch_compound_details_unified'
]

