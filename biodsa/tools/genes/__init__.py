"""Unified gene search and information tools.

This module provides unified access to multiple gene and variant databases including
BioThings (MyGene.info, MyVariant.info) and KEGG Gene Database.
"""

from .unified_gene_search import (
    search_genes_unified,
    fetch_gene_details_unified,
    aggregate_gene_symbols,
    aggregate_gene_identifiers,
)

__all__ = [
    'search_genes_unified',
    'fetch_gene_details_unified',
    'aggregate_gene_symbols',
    'aggregate_gene_identifiers',
]

