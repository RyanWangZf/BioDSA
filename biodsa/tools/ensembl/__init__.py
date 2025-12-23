"""
Ensembl Tools

Tools for interacting with the Ensembl genomics database.

This package provides comprehensive access to Ensembl's genomic data,
including gene information, sequences, variants, comparative genomics,
and assembly information.
"""

from .client import EnsemblClient

# Gene tools
from .gene_tools import (
    lookup_gene,
    get_transcripts,
    search_genes,
    get_gene_by_symbol,
    batch_gene_lookup
)

# Sequence tools
from .sequence_tools import (
    get_sequence,
    get_cds_sequence,
    translate_sequence,
    batch_sequence_fetch
)

# Comparative tools
from .comparative_tools import (
    get_homologs,
    get_gene_tree,
    compare_genes_across_species
)

# Variant tools
from .variant_tools import (
    get_variants,
    get_variant_info
)

# Regulatory tools
from .regulatory_tools import (
    get_regulatory_features,
    get_overlapping_features
)

# Annotation tools
from .annotation_tools import (
    get_xrefs,
    list_species,
    get_assembly_info,
    get_karyotype
)

__all__ = [
    # Client
    'EnsemblClient',
    
    # Gene tools
    'lookup_gene',
    'get_transcripts',
    'search_genes',
    'get_gene_by_symbol',
    'batch_gene_lookup',
    
    # Sequence tools
    'get_sequence',
    'get_cds_sequence',
    'translate_sequence',
    'batch_sequence_fetch',
    
    # Comparative tools
    'get_homologs',
    'get_gene_tree',
    'compare_genes_across_species',
    
    # Variant tools
    'get_variants',
    'get_variant_info',
    
    # Regulatory tools
    'get_regulatory_features',
    'get_overlapping_features',
    
    # Annotation tools
    'get_xrefs',
    'list_species',
    'get_assembly_info',
    'get_karyotype',
]

