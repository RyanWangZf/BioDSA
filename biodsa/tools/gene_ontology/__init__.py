"""Gene Ontology tools for BioDSA.

This module provides Python tools for interacting with the Gene Ontology (GO).
The Gene Ontology provides a framework and set of concepts for describing the functions
of gene products from all organisms.

Available Tools:
    - Term Tools: search_go_terms, get_go_term_details, get_go_term_hierarchy,
                  validate_go_id, get_ontology_statistics
    - Annotation Tools: get_gene_annotations, get_term_annotations, get_evidence_codes
    - Client: GeneOntologyClient for direct API access

Example Usage:
    >>> from biodsa.tools.gene_ontology import search_go_terms, get_gene_annotations
    >>> 
    >>> # Search for GO terms
    >>> df, output = search_go_terms("kinase activity", limit=10)
    >>> print(output)
    >>> 
    >>> # Get gene annotations
    >>> df, output = get_gene_annotations("P31749", taxon_id=9606)
    >>> print(df[['go_id', 'go_name', 'evidence_code']])
"""

from .client import GeneOntologyClient
from .term_tools import (
    search_go_terms,
    get_go_term_details,
    get_go_term_hierarchy,
    validate_go_id,
    get_ontology_statistics,
)
from .annotation_tools import (
    get_gene_annotations,
    get_term_annotations,
    get_evidence_codes,
)

__all__ = [
    # Client
    'GeneOntologyClient',
    
    # Term Tools
    'search_go_terms',
    'get_go_term_details',
    'get_go_term_hierarchy',
    'validate_go_id',
    'get_ontology_statistics',
    
    # Annotation Tools
    'get_gene_annotations',
    'get_term_annotations',
    'get_evidence_codes',
]

