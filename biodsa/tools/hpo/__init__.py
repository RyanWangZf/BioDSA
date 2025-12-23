"""Human Phenotype Ontology tools for BioDSA.

This module provides Python tools for interacting with the Human Phenotype Ontology (HPO).
The HPO provides a standardized vocabulary of phenotypic abnormalities encountered in human
disease. It contains over 18,000 terms describing clinical features and is widely used in
genetic research and clinical diagnostics.

Available Tools:
    - Term Tools: search_hpo_terms, get_hpo_term_details, get_hpo_term_hierarchy,
                  validate_hpo_id, get_hpo_term_path, compare_hpo_terms,
                  get_hpo_term_statistics, batch_get_hpo_terms
    - Client: HPOClient for direct API access

Example Usage:
    >>> from biodsa.tools.hpo import search_hpo_terms, get_hpo_term_details
    >>> 
    >>> # Search for HPO terms
    >>> df, output = search_hpo_terms("seizure", max_results=10)
    >>> print(output)
    >>> 
    >>> # Get term details
    >>> details, output = get_hpo_term_details("HP:0001250")
    >>> print(details['name'])
"""

from .client import HPOClient
from .term_tools import (
    search_hpo_terms,
    get_hpo_term_details,
    get_hpo_term_hierarchy,
    validate_hpo_id,
    get_hpo_term_path,
    compare_hpo_terms,
    get_hpo_term_statistics,
    batch_get_hpo_terms,
)

__all__ = [
    # Client
    'HPOClient',
    
    # Term Tools
    'search_hpo_terms',
    'get_hpo_term_details',
    'get_hpo_term_hierarchy',
    'validate_hpo_id',
    'get_hpo_term_path',
    'compare_hpo_terms',
    'get_hpo_term_statistics',
    'batch_get_hpo_terms',
]

