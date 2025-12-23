"""Client for the Human Phenotype Ontology (HPO) API

This module provides a Python client for interacting with the HPO API.
The Human Phenotype Ontology provides a standardized vocabulary of phenotypic
abnormalities encountered in human disease. It contains over 18,000 terms.

HPO API Documentation: https://hpo.jax.org/api/
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class HPOClient:
    """Client for interacting with the Human Phenotype Ontology API.
    
    This client provides methods for querying HPO including phenotype terms,
    hierarchical relationships, and term comparisons.
    """
    
    BASE_URL = "https://ontology.jax.org/api/hp"
    
    def __init__(self, timeout: int = 30):
        """Initialize the HPO client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-HPO-Client/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the HPO API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters (optional)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def normalize_hpo_id(hpo_id: str) -> str:
        """Normalize HPO identifier to standard format.
        
        Args:
            hpo_id: HPO identifier (e.g., "HP:0001234" or "0001234")
            
        Returns:
            Normalized HPO ID in format "HP:NNNNNNN"
            
        Examples:
            >>> client = HPOClient()
            >>> client.normalize_hpo_id("0001234")
            'HP:0001234'
            >>> client.normalize_hpo_id("HP:0001234")
            'HP:0001234'
        """
        if hpo_id.startswith('HP:'):
            return hpo_id
        if re.match(r'^\d{7}$', hpo_id):
            return f'HP:{hpo_id}'
        return hpo_id
    
    @staticmethod
    def validate_hpo_id_format(hpo_id: str) -> bool:
        """Validate HPO identifier format.
        
        Args:
            hpo_id: HPO identifier to validate
            
        Returns:
            True if format is valid, False otherwise
            
        Examples:
            >>> client = HPOClient()
            >>> client.validate_hpo_id_format("HP:0001234")
            True
            >>> client.validate_hpo_id_format("INVALID")
            False
        """
        return bool(re.match(r'^HP:\d{7}$', hpo_id))
    
    # Term Search and Retrieval
    
    def search_terms(
        self,
        query: str,
        max_results: int = 20,
        offset: int = 0,
        category: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for HPO terms by keyword, ID, or synonym.
        
        Args:
            query: Search query (term name, keyword, HPO ID, or synonym)
            max_results: Maximum number of results to return (default: 20)
            offset: Number of results to skip (default: 0)
            category: Filter by specific HPO categories (optional)
            
        Returns:
            Dictionary containing search results
            
        Examples:
            >>> client = HPOClient()
            >>> results = client.search_terms("seizure", max_results=10)
            >>> print(results['terms'])
        """
        params = {
            'q': query,
            'max': max_results,
            'offset': offset
        }
        
        if category:
            params['category'] = ','.join(category)
        
        return self._make_request('search', params=params)
    
    def get_term(self, hpo_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific HPO term.
        
        Args:
            hpo_id: HPO term identifier (e.g., "HP:0001234")
            
        Returns:
            Dictionary containing term information
            
        Examples:
            >>> client = HPOClient()
            >>> term = client.get_term("HP:0001250")
            >>> print(term['name'])
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        return self._make_request(f'terms/{hpo_id}')
    
    def get_all_terms(
        self,
        max_results: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get a list of all HPO terms with pagination.
        
        Args:
            max_results: Maximum number of terms to return (default: 20)
            offset: Number of terms to skip (default: 0)
            
        Returns:
            List of HPO terms
            
        Examples:
            >>> client = HPOClient()
            >>> terms = client.get_all_terms(max_results=50)
            >>> print(len(terms))
        """
        params = {
            'max': max_results,
            'offset': offset
        }
        response = self._make_request('terms', params=params)
        return response.get('terms', [])
    
    # Hierarchy Navigation
    
    def get_ancestors(
        self,
        hpo_id: str,
        max_results: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all ancestor terms for an HPO term.
        
        Args:
            hpo_id: HPO term identifier
            max_results: Maximum number of ancestors to return (default: 50)
            offset: Number of results to skip (default: 0)
            
        Returns:
            List of ancestor terms
            
        Examples:
            >>> client = HPOClient()
            >>> ancestors = client.get_ancestors("HP:0001250")
            >>> print(len(ancestors))
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        params = {
            'max': max_results,
            'offset': offset
        }
        response = self._make_request(f'terms/{hpo_id}/ancestors', params=params)
        # API returns list directly
        return response if isinstance(response, list) else response.get('terms', [])
    
    def get_parents(
        self,
        hpo_id: str,
        max_results: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get direct parent terms for an HPO term.
        
        Args:
            hpo_id: HPO term identifier
            max_results: Maximum number of parents to return (default: 20)
            offset: Number of results to skip (default: 0)
            
        Returns:
            List of parent terms
            
        Examples:
            >>> client = HPOClient()
            >>> parents = client.get_parents("HP:0001250")
            >>> print(parents)
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        params = {
            'max': max_results,
            'offset': offset
        }
        response = self._make_request(f'terms/{hpo_id}/parents', params=params)
        # API returns list directly
        return response if isinstance(response, list) else response.get('terms', [])
    
    def get_children(
        self,
        hpo_id: str,
        max_results: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get direct child terms for an HPO term.
        
        Args:
            hpo_id: HPO term identifier
            max_results: Maximum number of children to return (default: 20)
            offset: Number of results to skip (default: 0)
            
        Returns:
            List of child terms
            
        Examples:
            >>> client = HPOClient()
            >>> children = client.get_children("HP:0001250")
            >>> print(children)
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        params = {
            'max': max_results,
            'offset': offset
        }
        response = self._make_request(f'terms/{hpo_id}/children', params=params)
        # API returns list directly
        return response if isinstance(response, list) else response.get('terms', [])
    
    def get_descendants(
        self,
        hpo_id: str,
        max_results: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all descendant terms for an HPO term.
        
        Args:
            hpo_id: HPO term identifier
            max_results: Maximum number of descendants to return (default: 50)
            offset: Number of results to skip (default: 0)
            
        Returns:
            List of descendant terms
            
        Examples:
            >>> client = HPOClient()
            >>> descendants = client.get_descendants("HP:0001250")
            >>> print(len(descendants))
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        params = {
            'max': max_results,
            'offset': offset
        }
        response = self._make_request(f'terms/{hpo_id}/descendants', params=params)
        # API returns list directly
        return response if isinstance(response, list) else response.get('terms', [])
    
    # Utility Methods
    
    def validate_term(self, hpo_id: str) -> Dict[str, Any]:
        """Validate an HPO identifier.
        
        Args:
            hpo_id: HPO identifier to validate
            
        Returns:
            Dictionary with validation results
            
        Examples:
            >>> client = HPOClient()
            >>> result = client.validate_term("HP:0001250")
            >>> print(result['valid'])
        """
        normalized_id = self.normalize_hpo_id(hpo_id)
        is_valid_format = self.validate_hpo_id_format(normalized_id)
        
        exists = False
        term_info = None
        
        if is_valid_format:
            try:
                term_info = self.get_term(normalized_id)
                exists = term_info is not None and 'id' in term_info
            except Exception:
                exists = False
        
        return {
            'input_id': hpo_id,
            'normalized_id': normalized_id,
            'valid_format': is_valid_format,
            'exists': exists,
            'term_info': term_info,
            'format_rules': {
                'pattern': 'HP:NNNNNNN',
                'example': 'HP:0001250',
                'description': 'HPO identifiers consist of "HP:" followed by exactly 7 digits'
            }
        }
    
    def get_term_path(self, hpo_id: str) -> List[Dict[str, Any]]:
        """Get the full hierarchical path from root to a specific HPO term.
        
        Args:
            hpo_id: HPO term identifier
            
        Returns:
            List of terms from root to specified term
            
        Examples:
            >>> client = HPOClient()
            >>> path = client.get_term_path("HP:0001250")
            >>> print([term['name'] for term in path])
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        
        # Get the term itself
        term = self.get_term(hpo_id)
        
        # Get all ancestors
        ancestors = self.get_ancestors(hpo_id, max_results=200)
        
        # Build path from root to term
        path = list(reversed(ancestors))
        path.append(term)
        
        return path
    
    def compare_terms(
        self,
        term1_id: str,
        term2_id: str
    ) -> Dict[str, Any]:
        """Compare two HPO terms and find their relationship.
        
        Args:
            term1_id: First HPO term identifier
            term2_id: Second HPO term identifier
            
        Returns:
            Dictionary containing comparison results
            
        Examples:
            >>> client = HPOClient()
            >>> comparison = client.compare_terms("HP:0001250", "HP:0012469")
            >>> print(comparison['relationship'])
        """
        term1_id = self.normalize_hpo_id(term1_id)
        term2_id = self.normalize_hpo_id(term2_id)
        
        # Get term details
        term1 = self.get_term(term1_id)
        term2 = self.get_term(term2_id)
        
        # Get ancestors for both terms
        ancestors1 = self.get_ancestors(term1_id, max_results=200)
        ancestors2 = self.get_ancestors(term2_id, max_results=200)
        
        # Find common ancestors
        ancestors1_ids = {a['id'] for a in ancestors1}
        ancestors2_ids = {a['id'] for a in ancestors2}
        common_ancestor_ids = ancestors1_ids & ancestors2_ids
        common_ancestors = [a for a in ancestors1 if a['id'] in common_ancestor_ids]
        
        # Determine relationship
        relationship = 'No direct relationship'
        if term2_id in ancestors1_ids:
            relationship = f"{term1_id} is a descendant of {term2_id}"
        elif term1_id in ancestors2_ids:
            relationship = f"{term2_id} is a descendant of {term1_id}"
        elif common_ancestors:
            relationship = f"Related through common ancestors"
        
        return {
            'term1': term1,
            'term2': term2,
            'relationship': relationship,
            'common_ancestors': common_ancestors,
            'term1_depth': len(ancestors1),
            'term2_depth': len(ancestors2)
        }
    
    def get_term_statistics(self, hpo_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an HPO term.
        
        Args:
            hpo_id: HPO term identifier
            
        Returns:
            Dictionary containing term statistics
            
        Examples:
            >>> client = HPOClient()
            >>> stats = client.get_term_statistics("HP:0001250")
            >>> print(stats)
        """
        hpo_id = self.normalize_hpo_id(hpo_id)
        
        # Get term details and relationships
        term = self.get_term(hpo_id)
        ancestors = self.get_ancestors(hpo_id, max_results=1000)
        descendants = self.get_descendants(hpo_id, max_results=1000)
        parents = self.get_parents(hpo_id, max_results=100)
        children = self.get_children(hpo_id, max_results=100)
        
        return {
            'term_id': hpo_id,
            'term_name': term.get('name'),
            'definition': term.get('definition'),
            'hierarchy': {
                'depth_from_root': len(ancestors),
                'ancestor_count': len(ancestors),
                'parent_count': len(parents),
                'child_count': len(children),
                'descendant_count': len(descendants)
            },
            'properties': {
                'synonyms': term.get('synonyms', []),
                'xrefs': term.get('xrefs', []),
                'alternative_ids': term.get('alternativeIds', []),
                'is_obsolete': term.get('isObsolete', False),
                'comment': term.get('comment')
            }
        }
    
    def batch_get_terms(self, hpo_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple HPO terms in a single batch.
        
        Args:
            hpo_ids: List of HPO term identifiers (maximum 20)
            
        Returns:
            List of term information dictionaries
            
        Examples:
            >>> client = HPOClient()
            >>> terms = client.batch_get_terms(["HP:0001250", "HP:0012469"])
            >>> print([t.get('name') for t in terms if t])
        """
        results = []
        for hpo_id in hpo_ids[:20]:  # Limit to 20
            try:
                term = self.get_term(hpo_id)
                results.append({
                    'id': hpo_id,
                    'success': True,
                    'data': term
                })
            except Exception as e:
                results.append({
                    'id': hpo_id,
                    'success': False,
                    'error': str(e)
                })
        return results

