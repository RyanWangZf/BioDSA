"""ChEMBL Database tools for BioDSA.

This module provides Python tools for interacting with the ChEMBL Database API.
ChEMBL is a manually curated database of bioactive molecules with drug-like properties.

Available Tools:
    - Compound Tools: search_compounds, get_compound_details, search_similar_compounds, 
                      search_substructure, batch_compound_lookup
    - Drug Tools: get_drug_indications, get_drug_mechanisms, get_drug_clinical_data,
                  search_drugs_by_indication
    - Target Tools: search_targets, get_target_details, search_by_uniprot,
                    get_target_bioactivities, get_compounds_for_target
    - Client: ChEMBLClient for direct API access

Example Usage:
    >>> from biodsa.tools.chembl import search_compounds, get_compound_details
    >>> from biodsa.tools.chembl import get_drug_indications, search_targets
    >>> 
    >>> # Search for compounds
    >>> df, output = search_compounds("aspirin", limit=10)
    >>> print(output)
    >>> 
    >>> # Get compound details
    >>> details, output = get_compound_details("CHEMBL25")
    >>> print(details['molecule_properties'])
    >>> 
    >>> # Get drug indications
    >>> df, output = get_drug_indications(molecule_chembl_id="CHEMBL25")
    >>> print(output)
    >>> 
    >>> # Search for targets
    >>> df, output = search_targets("kinase", limit=10)
    >>> print(output)
"""

from .client import ChEMBLClient
from .compound_tools import (
    search_compounds,
    get_compound_details,
    search_similar_compounds,
    search_substructure,
    batch_compound_lookup,
)
from .drug_tools import (
    get_drug_indications,
    get_drug_mechanisms,
    get_drug_clinical_data,
    search_drugs_by_indication,
)
from .target_tools import (
    search_targets,
    get_target_details,
    search_by_uniprot,
    get_target_bioactivities,
    get_compounds_for_target,
)

__all__ = [
    # Client
    'ChEMBLClient',
    
    # Compound Tools
    'search_compounds',
    'get_compound_details',
    'search_similar_compounds',
    'search_substructure',
    'batch_compound_lookup',
    
    # Drug Tools
    'get_drug_indications',
    'get_drug_mechanisms',
    'get_drug_clinical_data',
    'search_drugs_by_indication',
    
    # Target Tools
    'search_targets',
    'get_target_details',
    'search_by_uniprot',
    'get_target_bioactivities',
    'get_compounds_for_target',
]

