"""Open Targets Platform tools for BioDSA.

This module provides Python tools for interacting with the Open Targets Platform API,
including target search, disease search, drug search, and target-disease association analysis.

Open Targets Platform is a comprehensive resource for target identification and validation,
combining multiple data sources to provide evidence for target-disease associations.

Available Tools:
    - Target Tools: search_targets, get_target_details, get_target_associated_diseases
    - Disease Tools: search_diseases, get_disease_details, get_disease_associated_targets, get_disease_targets_summary
    - Association Tools: get_target_disease_evidence, analyze_association_evidence
    - Drug Tools: search_drugs, get_drug_details

Example Usage:
    >>> from biodsa.tools.opentargets import search_targets, get_disease_associated_targets
    >>> 
    >>> # Search for targets
    >>> df, output = search_targets("BRCA1", size=10)
    >>> print(output)
    >>> 
    >>> # Get targets for a disease
    >>> df, output = get_disease_associated_targets("EFO_0000508", size=20, min_score=0.5)
    >>> print(df[['target_symbol', 'target_name', 'score']])
"""

from .client import OpenTargetsClient
from .target_tools import (
    search_targets,
    get_target_details,
    get_target_associated_diseases,
)
from .disease_tools import (
    search_diseases,
    get_disease_details,
    get_disease_associated_targets,
    get_disease_targets_summary,
)
from .association_tools import (
    get_target_disease_evidence,
    analyze_association_evidence,
)
from .drug_tools import (
    search_drugs,
    get_drug_details,
)

__all__ = [
    # Client
    'OpenTargetsClient',
    
    # Target Tools
    'search_targets',
    'get_target_details',
    'get_target_associated_diseases',
    
    # Disease Tools
    'search_diseases',
    'get_disease_details',
    'get_disease_associated_targets',
    'get_disease_targets_summary',
    
    # Association Tools
    'get_target_disease_evidence',
    'analyze_association_evidence',
    
    # Drug Tools
    'search_drugs',
    'get_drug_details',
]
