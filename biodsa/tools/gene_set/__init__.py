"""Gene set analysis API functions.

This module provides pure API functions without LangChain dependencies.
Functions for gene set analysis and single gene information retrieval.
"""

__all__ = [
    # Gene set functions
    "get_pathway_for_gene_set",
    "get_enrichment_for_gene_set",
    "get_interactions_for_gene_set",
    "get_complex_for_gene_set",
    # Single gene functions
    "get_gene_summary_for_single_gene",
    "get_disease_for_single_gene",
    "get_domain_for_single_gene",
]

from .get_pathway_for_gene_set import get_pathway_for_gene_set
from .get_enrichment_for_gene_set import get_enrichment_for_gene_set
from .get_interactions_for_gene_set import get_interactions_for_gene_set
from .get_complex_for_gene_set import get_complex_for_gene_set
from .get_gene_summary_for_single_gene import get_gene_summary_for_single_gene
from .get_disease_for_single_gene import get_disease_for_single_gene
from .get_domain_for_single_gene import get_domain_for_single_gene
