"""
OpenGenes API Tools

This module provides access to the OpenGenes database of aging and longevity genes.
"""

from biodsa.tools.opengenes.client import OpenGenesClient
from biodsa.tools.opengenes.gene_tools import (
    search_genes,
    get_gene_by_symbol,
    get_gene_by_ncbi_id,
    get_latest_genes,
    get_genes_increase_lifespan,
    get_gene_symbols,
    get_genes_by_go_term,
)
from biodsa.tools.opengenes.taxonomy_tools import (
    get_model_organisms,
    get_phylums,
)
from biodsa.tools.opengenes.protein_tools import (
    get_protein_classes,
)
from biodsa.tools.opengenes.disease_tools import (
    get_diseases,
    get_disease_categories,
)
from biodsa.tools.opengenes.research_tools import (
    get_calorie_experiments,
    get_aging_mechanisms,
)

__all__ = [
    # Client
    'OpenGenesClient',
    # Gene operations
    'search_genes',
    'get_gene_by_symbol',
    'get_gene_by_ncbi_id',
    'get_latest_genes',
    'get_genes_increase_lifespan',
    'get_gene_symbols',
    'get_genes_by_go_term',
    # Taxonomy operations
    'get_model_organisms',
    'get_phylums',
    # Protein operations
    'get_protein_classes',
    # Disease operations
    'get_diseases',
    'get_disease_categories',
    # Research operations
    'get_calorie_experiments',
    'get_aging_mechanisms',
]

