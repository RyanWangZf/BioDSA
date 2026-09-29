"""
UniProt Tools

Tools for interacting with the UniProt protein database.

This package provides comprehensive access to UniProt's protein data,
including sequence information, structural features, functional annotations,
and evolutionary relationships.
"""

from .client import UniProtClient

# Protein tools
from .protein_tools import (
    search_proteins,
    get_protein_info,
    search_by_gene,
    get_protein_features,
    validate_accession
)

# Sequence tools
from .sequence_tools import (
    get_protein_sequence,
    analyze_sequence_composition,
    export_protein_data
)

# Comparative tools
from .comparative_tools import (
    compare_proteins,
    get_protein_homologs,
    get_protein_orthologs,
    get_phylogenetic_info,
    get_taxonomy_info
)

# Structure tools
from .structure_tools import (
    get_protein_structure,
    get_protein_domains_detailed,
    get_protein_variants,
    get_annotation_confidence
)

# Biological context tools
from .biological_context_tools import (
    get_protein_pathways,
    get_protein_interactions,
    search_by_function,
    search_by_localization,
    get_external_references,
    get_literature_references
)

# Advanced search tools
from .advanced_search_tools import (
    batch_protein_lookup,
    advanced_search,
    search_by_taxonomy
)

__all__ = [
    # Client
    'UniProtClient',
    
    # Protein tools
    'search_proteins',
    'get_protein_info',
    'search_by_gene',
    'get_protein_features',
    'validate_accession',
    
    # Sequence tools
    'get_protein_sequence',
    'analyze_sequence_composition',
    'export_protein_data',
    
    # Comparative tools
    'compare_proteins',
    'get_protein_homologs',
    'get_protein_orthologs',
    'get_phylogenetic_info',
    'get_taxonomy_info',
    
    # Structure tools
    'get_protein_structure',
    'get_protein_domains_detailed',
    'get_protein_variants',
    'get_annotation_confidence',
    
    # Biological context tools
    'get_protein_pathways',
    'get_protein_interactions',
    'search_by_function',
    'search_by_localization',
    'get_external_references',
    'get_literature_references',
    
    # Advanced search tools
    'batch_protein_lookup',
    'advanced_search',
    'search_by_taxonomy',
]
