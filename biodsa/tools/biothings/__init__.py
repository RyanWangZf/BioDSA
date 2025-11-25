"""BioThings data search and access functions.

This module provides tools for searching and accessing biological data including
genes, diseases, and drugs from MyGene.info, MyDisease.info, and MyChem.info APIs.
"""

__all__ = [
    # Functions
    "search_genes",
    "search_diseases", 
    "search_drugs",
    "search_variants",
    "fetch_gene_details_by_ids",
    "fetch_disease_details_by_ids",
    "fetch_drug_details_by_ids",
    "fetch_variant_details_by_ids",
]

from .genes import search_genes, fetch_gene_details_by_ids
from .diseases import search_diseases, fetch_disease_details_by_ids
from .drugs import search_drugs, fetch_drug_details_by_ids
from .variants import search_variants, fetch_variant_details_by_ids