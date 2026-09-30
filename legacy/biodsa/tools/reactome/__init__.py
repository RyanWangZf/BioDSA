"""
Reactome API Tools

This module provides access to Reactome's curated biological pathway data.
"""

from biodsa.tools.reactome.client import ReactomeClient
from biodsa.tools.reactome.pathway_tools import (
    search_pathways,
    get_pathway_details,
    get_pathway_hierarchy,
    get_pathway_reactions,
    get_pathway_participants,
)
from biodsa.tools.reactome.gene_tools import (
    find_pathways_by_gene,
    get_gene_pathways_dataframe,
    get_protein_interactions,
)
from biodsa.tools.reactome.disease_tools import (
    find_pathways_by_disease,
)

__all__ = [
    # Client
    'ReactomeClient',
    # Pathway operations
    'search_pathways',
    'get_pathway_details',
    'get_pathway_hierarchy',
    'get_pathway_reactions',
    'get_pathway_participants',
    # Gene/protein operations
    'find_pathways_by_gene',
    'get_gene_pathways_dataframe',
    'get_protein_interactions',
    # Disease operations
    'find_pathways_by_disease',
]

