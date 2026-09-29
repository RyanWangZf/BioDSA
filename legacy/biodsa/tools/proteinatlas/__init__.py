"""
Human Protein Atlas Tools

Tools for interacting with the Human Protein Atlas database.

This package provides comprehensive access to protein expression data,
subcellular localization, pathology information, and antibody validation
data from the Human Protein Atlas.
"""

from .client import ProteinAtlasClient

# Protein tools
from .protein_tools import (
    search_proteins,
    get_protein_info,
    batch_protein_lookup,
    get_protein_classes,
    advanced_search
)

# Expression tools
from .expression_tools import (
    get_tissue_expression,
    get_blood_expression,
    get_brain_expression,
    search_by_tissue,
    compare_expression_profiles
)

# Subcellular localization tools
from .subcellular_tools import (
    get_subcellular_location,
    search_by_subcellular_location
)

# Pathology tools
from .pathology_tools import (
    get_pathology_data,
    search_cancer_markers
)

# Antibody tools
from .antibody_tools import (
    get_antibody_info
)

__all__ = [
    # Client
    'ProteinAtlasClient',
    
    # Protein tools
    'search_proteins',
    'get_protein_info',
    'batch_protein_lookup',
    'get_protein_classes',
    'advanced_search',
    
    # Expression tools
    'get_tissue_expression',
    'get_blood_expression',
    'get_brain_expression',
    'search_by_tissue',
    'compare_expression_profiles',
    
    # Subcellular localization tools
    'get_subcellular_location',
    'search_by_subcellular_location',
    
    # Pathology tools
    'get_pathology_data',
    'search_cancer_markers',
    
    # Antibody tools
    'get_antibody_info',
]

