"""
PubChem Tools

Tools for interacting with the PubChem database for chemical compound information.

This package provides comprehensive access to PubChem data including:
- Compound search and retrieval
- Structure similarity and substructure search
- Chemical properties and descriptors
- Bioassay and activity data
- Safety and toxicity information
- External database cross-references
"""

from .client import PubChemClient

# Compound tools
from .compound_tools import (
    search_compounds,
    get_compound_info,
    get_compound_synonyms,
    search_by_smiles,
    search_by_inchi,
    search_by_cas_number,
    batch_compound_lookup
)

# Structure tools
from .structure_tools import (
    search_similar_compounds,
    substructure_search,
    superstructure_search,
    get_3d_conformers,
    analyze_stereochemistry
)

# Property tools
from .property_tools import (
    get_compound_properties,
    calculate_descriptors,
    assess_drug_likeness,
    analyze_molecular_complexity
)

# Bioassay tools
from .bioassay_tools import (
    get_assay_info,
    get_compound_bioactivities,
    compare_activity_profiles
)

# Safety tools
from .safety_tools import (
    get_safety_data,
    get_toxicity_info
)

# Reference tools
from .reference_tools import (
    get_external_references,
    get_literature_references
)

__all__ = [
    # Client
    'PubChemClient',
    
    # Compound tools
    'search_compounds',
    'get_compound_info',
    'get_compound_synonyms',
    'search_by_smiles',
    'search_by_inchi',
    'search_by_cas_number',
    'batch_compound_lookup',
    
    # Structure tools
    'search_similar_compounds',
    'substructure_search',
    'superstructure_search',
    'get_3d_conformers',
    'analyze_stereochemistry',
    
    # Property tools
    'get_compound_properties',
    'calculate_descriptors',
    'assess_drug_likeness',
    'analyze_molecular_complexity',
    
    # Bioassay tools
    'get_assay_info',
    'get_compound_bioactivities',
    'compare_activity_profiles',
    
    # Safety tools
    'get_safety_data',
    'get_toxicity_info',
    
    # Reference tools
    'get_external_references',
    'get_literature_references',
]

