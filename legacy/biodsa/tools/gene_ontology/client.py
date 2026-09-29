"""Client for the Gene Ontology (GO) API

This module provides a Python client for interacting with Gene Ontology APIs.
The Gene Ontology provides a framework for the model of biology, with three ontologies:
molecular function, cellular component, and biological process.

Gene Ontology API Documentation: https://www.ebi.ac.uk/QuickGO/api/index.html
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class GeneOntologyClient:
    """Client for interacting with the Gene Ontology APIs.
    
    This client provides methods for querying Gene Ontology including GO terms,
    annotations, enrichment analysis, and term relationships.
    """
    
    QUICKGO_BASE_URL = "https://www.ebi.ac.uk/QuickGO/services"
    GO_API_BASE_URL = "https://api.geneontology.org"
    
    # GO ontology namespaces
    MOLECULAR_FUNCTION = "molecular_function"
    BIOLOGICAL_PROCESS = "biological_process"
    CELLULAR_COMPONENT = "cellular_component"
    
    # Aspect codes
    ASPECT_MAP = {
        MOLECULAR_FUNCTION: "F",
        BIOLOGICAL_PROCESS: "P",
        CELLULAR_COMPONENT: "C"
    }
    
    def __init__(self, timeout: int = 30):
        """Initialize the Gene Ontology client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-GO-Client/1.0',
            'Accept': 'application/json'
        })
    
    def _make_quickgo_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the QuickGO API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters (optional)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.QUICKGO_BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def _make_go_api_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the GO API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters (optional)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.GO_API_BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def normalize_go_id(go_id: str) -> str:
        """Normalize GO identifier to standard format.
        
        Args:
            go_id: GO identifier (e.g., "GO:0008150" or "0008150")
            
        Returns:
            Normalized GO ID in format "GO:NNNNNNN"
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> client.normalize_go_id("0008150")
            'GO:0008150'
            >>> client.normalize_go_id("GO:0008150")
            'GO:0008150'
        """
        if go_id.startswith('GO:'):
            return go_id
        if re.match(r'^\d{7}$', go_id):
            return f'GO:{go_id}'
        return go_id
    
    @staticmethod
    def validate_go_id_format(go_id: str) -> bool:
        """Validate GO identifier format.
        
        Args:
            go_id: GO identifier to validate
            
        Returns:
            True if format is valid, False otherwise
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> client.validate_go_id_format("GO:0008150")
            True
            >>> client.validate_go_id_format("INVALID")
            False
        """
        return bool(re.match(r'^GO:\d{7}$', go_id))
    
    # Term Search and Retrieval
    
    def search_terms(
        self,
        query: str,
        ontology: Optional[str] = None,
        limit: int = 25,
        exact: bool = False,
        include_obsolete: bool = False
    ) -> Dict[str, Any]:
        """Search across Gene Ontology terms.
        
        Args:
            query: Search query (term name, keyword, or definition)
            ontology: GO ontology to search ("molecular_function", "biological_process",
                     "cellular_component", or None for all)
            limit: Number of results to return (1-500, default: 25)
            exact: Exact match only (default: False)
            include_obsolete: Include obsolete terms (default: False)
            
        Returns:
            Dictionary containing search results
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> results = client.search_terms("kinase activity", limit=10)
            >>> print(results['numberOfHits'])
        """
        params = {
            'query': query,
            'limit': min(limit, 500),
            'page': 1
        }
        
        if ontology and ontology != 'all':
            params['aspect'] = self.ASPECT_MAP.get(ontology, ontology)
        
        if not include_obsolete:
            params['obsolete'] = 'false'
        
        return self._make_quickgo_request('ontology/go/search', params=params)
    
    def get_term(self, go_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific GO term.
        
        Args:
            go_id: GO term identifier (e.g., "GO:0008150")
            
        Returns:
            Dictionary containing term information
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> term = client.get_term("GO:0008150")
            >>> print(term['results'][0]['name'])
        """
        go_id = self.normalize_go_id(go_id)
        return self._make_quickgo_request(f'ontology/go/terms/{go_id}')
    
    def get_term_ancestors(
        self,
        go_id: str,
        relations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get ancestor terms (parent terms) for a GO term.
        
        Args:
            go_id: GO term identifier
            relations: List of relations to traverse (e.g., ["is_a", "part_of"])
            
        Returns:
            Dictionary containing ancestor terms
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> ancestors = client.get_term_ancestors("GO:0004672")
        """
        go_id = self.normalize_go_id(go_id)
        params = {}
        if relations:
            params['relations'] = ','.join(relations)
        
        return self._make_quickgo_request(
            f'ontology/go/terms/{go_id}/ancestors',
            params=params
        )
    
    def get_term_descendants(
        self,
        go_id: str,
        relations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get descendant terms (child terms) for a GO term.
        
        Args:
            go_id: GO term identifier
            relations: List of relations to traverse (e.g., ["is_a", "part_of"])
            
        Returns:
            Dictionary containing descendant terms
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> descendants = client.get_term_descendants("GO:0004672")
        """
        go_id = self.normalize_go_id(go_id)
        params = {}
        if relations:
            params['relations'] = ','.join(relations)
        
        return self._make_quickgo_request(
            f'ontology/go/terms/{go_id}/descendants',
            params=params
        )
    
    def get_term_children(self, go_id: str) -> Dict[str, Any]:
        """Get direct children (one level down) for a GO term.
        
        Args:
            go_id: GO term identifier
            
        Returns:
            Dictionary containing child terms
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> children = client.get_term_children("GO:0008150")
        """
        go_id = self.normalize_go_id(go_id)
        return self._make_quickgo_request(f'ontology/go/terms/{go_id}/children')
    
    # Annotation Methods
    
    def get_annotations(
        self,
        go_id: Optional[str] = None,
        gene_product_id: Optional[str] = None,
        taxon_id: Optional[Union[int, str]] = None,
        evidence_code: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get GO annotations.
        
        Args:
            go_id: GO term identifier filter
            gene_product_id: Gene product identifier filter (e.g., UniProt ID)
            taxon_id: NCBI taxonomy ID filter (e.g., 9606 for human)
            evidence_code: Evidence code filter (e.g., "IDA", "IEA")
            limit: Number of results to return (default: 100)
            
        Returns:
            Dictionary containing annotation data
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> annotations = client.get_annotations(
            ...     go_id="GO:0004672",
            ...     taxon_id=9606
            ... )
        """
        params = {'limit': limit}
        
        if go_id:
            params['goId'] = self.normalize_go_id(go_id)
        if gene_product_id:
            params['geneProductId'] = gene_product_id
        if taxon_id:
            params['taxonId'] = str(taxon_id)
        if evidence_code:
            params['evidenceCode'] = evidence_code
        
        return self._make_quickgo_request('annotation/search', params=params)
    
    def get_gene_annotations(
        self,
        gene_product_id: str,
        taxon_id: Optional[Union[int, str]] = None,
        ontology: Optional[str] = None,
        evidence_code: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get GO annotations for a specific gene.
        
        Args:
            gene_product_id: Gene product identifier (e.g., UniProt ID)
            taxon_id: NCBI taxonomy ID (e.g., 9606 for human)
            ontology: GO ontology filter
            evidence_code: Evidence code filter
            limit: Number of results to return (default: 100)
            
        Returns:
            Dictionary containing gene annotations
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> annotations = client.get_gene_annotations("P31749", taxon_id=9606)
        """
        params = {
            'geneProductId': gene_product_id,
            'limit': limit
        }
        
        if taxon_id:
            params['taxonId'] = str(taxon_id)
        if ontology and ontology != 'all':
            params['aspect'] = self.ASPECT_MAP.get(ontology, ontology)
        if evidence_code:
            params['evidenceCode'] = evidence_code
        
        return self._make_quickgo_request('annotation/search', params=params)
    
    # Statistics and Metadata
    
    def get_ontology_statistics(self) -> Dict[str, Any]:
        """Get statistics about GO ontologies.
        
        Returns:
            Dictionary containing ontology statistics
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> stats = client.get_ontology_statistics()
        """
        return {
            'ontologies': {
                'molecular_function': {
                    'description': 'Molecular activities of gene products',
                    'root_term': 'GO:0003674',
                    'aspect': 'F'
                },
                'biological_process': {
                    'description': 'Larger processes accomplished by multiple molecular activities',
                    'root_term': 'GO:0008150',
                    'aspect': 'P'
                },
                'cellular_component': {
                    'description': 'Locations relative to cellular structures',
                    'root_term': 'GO:0005575',
                    'aspect': 'C'
                }
            },
            'evidence_codes': {
                'experimental': {
                    'codes': ['EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP'],
                    'description': 'Inferred from direct experimental evidence'
                },
                'high_throughput': {
                    'codes': ['HTP', 'HDA', 'HMP', 'HGI', 'HEP'],
                    'description': 'High-throughput experimental evidence'
                },
                'computational': {
                    'codes': ['IBA', 'IBD', 'IKR', 'IRD', 'ISS', 'ISO', 'ISA', 'ISM', 'IGC', 'RCA'],
                    'description': 'Computational analysis evidence'
                },
                'author_statement': {
                    'codes': ['TAS', 'NAS'],
                    'description': 'Traceable/Non-traceable author statement'
                },
                'curator_statement': {
                    'codes': ['IC', 'ND'],
                    'description': 'Inferred by curator or no data available'
                },
                'electronic': {
                    'codes': ['IEA'],
                    'description': 'Inferred from electronic annotation'
                }
            },
            'resources': {
                'quickgo': 'https://www.ebi.ac.uk/QuickGO/',
                'amigo': 'http://amigo.geneontology.org/',
                'go_consortium': 'https://geneontology.org/'
            }
        }
    
    def get_evidence_codes(self) -> List[Dict[str, str]]:
        """Get list of GO evidence codes.
        
        Returns:
            List of evidence code information
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> codes = client.get_evidence_codes()
        """
        return [
            {'code': 'EXP', 'category': 'experimental', 'name': 'Inferred from Experiment'},
            {'code': 'IDA', 'category': 'experimental', 'name': 'Inferred from Direct Assay'},
            {'code': 'IPI', 'category': 'experimental', 'name': 'Inferred from Physical Interaction'},
            {'code': 'IMP', 'category': 'experimental', 'name': 'Inferred from Mutant Phenotype'},
            {'code': 'IGI', 'category': 'experimental', 'name': 'Inferred from Genetic Interaction'},
            {'code': 'IEP', 'category': 'experimental', 'name': 'Inferred from Expression Pattern'},
            {'code': 'HTP', 'category': 'high_throughput', 'name': 'High Throughput Experiment'},
            {'code': 'HDA', 'category': 'high_throughput', 'name': 'High Throughput Direct Assay'},
            {'code': 'HMP', 'category': 'high_throughput', 'name': 'High Throughput Mutant Phenotype'},
            {'code': 'HGI', 'category': 'high_throughput', 'name': 'High Throughput Genetic Interaction'},
            {'code': 'HEP', 'category': 'high_throughput', 'name': 'High Throughput Expression Pattern'},
            {'code': 'IBA', 'category': 'computational', 'name': 'Inferred from Biological aspect of Ancestor'},
            {'code': 'IBD', 'category': 'computational', 'name': 'Inferred from Biological aspect of Descendant'},
            {'code': 'IKR', 'category': 'computational', 'name': 'Inferred from Key Residues'},
            {'code': 'IRD', 'category': 'computational', 'name': 'Inferred from Rapid Divergence'},
            {'code': 'ISS', 'category': 'computational', 'name': 'Inferred from Sequence or structural Similarity'},
            {'code': 'ISO', 'category': 'computational', 'name': 'Inferred from Sequence Orthology'},
            {'code': 'ISA', 'category': 'computational', 'name': 'Inferred from Sequence Alignment'},
            {'code': 'ISM', 'category': 'computational', 'name': 'Inferred from Sequence Model'},
            {'code': 'IGC', 'category': 'computational', 'name': 'Inferred from Genomic Context'},
            {'code': 'RCA', 'category': 'computational', 'name': 'Inferred from Reviewed Computational Analysis'},
            {'code': 'TAS', 'category': 'author_statement', 'name': 'Traceable Author Statement'},
            {'code': 'NAS', 'category': 'author_statement', 'name': 'Non-traceable Author Statement'},
            {'code': 'IC', 'category': 'curator_statement', 'name': 'Inferred by Curator'},
            {'code': 'ND', 'category': 'curator_statement', 'name': 'No biological Data available'},
            {'code': 'IEA', 'category': 'electronic', 'name': 'Inferred from Electronic Annotation'}
        ]
    
    # Utility Methods
    
    def validate_term(self, go_id: str) -> Dict[str, Any]:
        """Validate a GO identifier.
        
        Args:
            go_id: GO identifier to validate
            
        Returns:
            Dictionary with validation results
            
        Examples:
            >>> client = GeneOntologyClient()
            >>> result = client.validate_term("GO:0008150")
            >>> print(result['valid'])
        """
        normalized_id = self.normalize_go_id(go_id)
        is_valid_format = self.validate_go_id_format(normalized_id)
        
        exists = False
        term_info = None
        
        if is_valid_format:
            try:
                response = self.get_term(normalized_id)
                results = response.get('results', [])
                if results:
                    term_info = results[0]
                    exists = True
            except Exception:
                exists = False
        
        return {
            'input_id': go_id,
            'normalized_id': normalized_id,
            'valid_format': is_valid_format,
            'exists': exists,
            'term_info': term_info,
            'format_rules': {
                'pattern': 'GO:NNNNNNN',
                'example': 'GO:0008150',
                'description': 'GO identifiers consist of "GO:" followed by exactly 7 digits'
            }
        }

