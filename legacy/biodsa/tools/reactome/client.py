"""
Reactome API Client

This module provides a Python client for the Reactome Content Service API.
API Documentation: https://reactome.org/ContentService/
"""

import os
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ReactomeClient:
    """Client for interacting with Reactome Content Service API."""
    
    def __init__(
        self,
        base_url: str = "https://reactome.org/ContentService",
        timeout: int = 45
    ):
        """
        Initialize the Reactome API client.
        
        Note: The Reactome API can be slow, especially for complex queries.
        Default timeout is set to 45 seconds.
        
        Args:
            base_url: Base URL for the Reactome Content Service API
            timeout: Request timeout in seconds (default: 45)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'BioDSA-Reactome-Client/1.0.0',
            'Content-Type': 'application/json',
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Make an HTTP request to the Reactome API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            timeout: Optional timeout override in seconds
            
        Returns:
            API response as dictionary or list
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_timeout = timeout if timeout is not None else self.timeout
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=request_timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Reactome API request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> Union[Dict[str, Any], List[Any]]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params, timeout=timeout)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Any]]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, data=data)
    
    # Search Operations
    
    def search_query(
        self,
        query: str,
        entity_type: Optional[str] = None,
        cluster: bool = True
    ) -> Dict[str, Any]:
        """
        Search Reactome database for pathways, reactions, proteins, etc.
        
        Args:
            query: Search query string
            entity_type: Type of entity to search (pathway, reaction, protein, complex, disease)
            cluster: Whether to cluster results by type
            
        Returns:
            Search results
        """
        params = {
            'query': query,
            'cluster': str(cluster).lower()
        }
        
        if entity_type:
            params['types'] = entity_type.capitalize()
        
        return self.get('/search/query', params=params)
    
    def resolve_pathway_id(self, identifier: str) -> Optional[str]:
        """
        Resolve a pathway name or identifier to a stable Reactome ID.
        
        Args:
            identifier: Pathway name or stable identifier
            
        Returns:
            Stable identifier (e.g., R-HSA-1234567) or None if not found
        """
        # If it's already a stable identifier, return it
        if identifier.startswith('R-') and '-' in identifier[2:]:
            return identifier
        
        # Search for the pathway by name
        try:
            results = self.search_query(query=identifier, entity_type='Pathway')
            
            if results.get('results'):
                for group in results['results']:
                    if group.get('entries') and len(group['entries']) > 0:
                        return group['entries'][0].get('stId')
        except Exception:
            pass
        
        return None
    
    # Pathway Operations
    
    def get_pathway_data(self, pathway_id: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific pathway.
        
        Args:
            pathway_id: Reactome pathway stable identifier
            
        Returns:
            Pathway data
        """
        return self.get(f'/data/query/{pathway_id}')
    
    def get_pathway_hierarchy(self, pathway_id: str) -> Dict[str, Any]:
        """
        Get hierarchical structure for a pathway.
        
        Args:
            pathway_id: Reactome pathway stable identifier
            
        Returns:
            Pathway hierarchy information
        """
        return self.get(f'/data/query/{pathway_id}')
    
    def get_pathway_events(self, pathway_id: str) -> List[Dict[str, Any]]:
        """
        Get all events contained in a pathway.
        
        Args:
            pathway_id: Reactome pathway stable identifier
            
        Returns:
            List of events
        """
        return self.get(f'/data/pathway/{pathway_id}/containedEvents')
    
    def get_pathway_participants(self, pathway_id: str) -> List[Dict[str, Any]]:
        """
        Get participating molecules in a pathway.
        
        Args:
            pathway_id: Reactome pathway stable identifier
            
        Returns:
            List of participating molecules
        """
        return self.get(f'/data/pathway/{pathway_id}/participatingMolecules')
    
    # Gene/Protein Operations
    
    def get_pathways_by_entity(self, entity_id: str, timeout: int = 20) -> List[Dict[str, Any]]:
        """
        Get pathways containing a specific entity (gene/protein).
        Note: This endpoint can be slow for proteins in many pathways (e.g., TP53, BRCA1).
        
        Args:
            entity_id: Entity stable identifier
            timeout: Request timeout in seconds (default: 20)
            
        Returns:
            List of pathways
        """
        return self.get(f'/data/pathways/low/entity/{entity_id}', timeout=timeout)
    
    def search_protein(
        self,
        gene_symbol: str,
        species: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for protein entities by gene symbol.
        
        Args:
            gene_symbol: Gene symbol (e.g., BRCA1, TP53)
            species: Species name filter
            
        Returns:
            Search results for proteins
        """
        return self.search_query(query=gene_symbol, entity_type='Protein')
    
    # Orthology Operations
    
    def get_orthologous_pathways(
        self,
        pathway_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get orthologous pathways for a given pathway.
        
        Args:
            pathway_id: Reactome pathway stable identifier
            
        Returns:
            List of orthologous pathways
        """
        try:
            return self.get(f'/data/orthologous/{pathway_id}/pathways')
        except Exception:
            return []

