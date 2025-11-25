"""
UniProt API Client

This module provides a client for interacting with the UniProt REST API.
UniProt is a comprehensive resource for protein sequence and annotation data.

API Documentation: https://www.uniprot.org/help/api
"""

import requests
from typing import Dict, Any, Optional, List
import time


class UniProtClient:
    """Client for the UniProt REST API."""
    
    def __init__(self, base_url: str = "https://rest.uniprot.org", timeout: int = 30):
        """
        Initialize the UniProt API client.
        
        Args:
            base_url: Base URL for the UniProt API (default: https://rest.uniprot.org)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-UniProt-Client/0.1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the UniProt API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"API request failed: {str(e)}")
    
    def search_proteins(
        self,
        query: str,
        organism: Optional[str] = None,
        size: int = 25,
        format: str = 'json'
    ) -> Any:
        """
        Search UniProt database for proteins.
        
        Args:
            query: Search query (protein name, keyword, or complex search)
            organism: Organism name or taxonomy ID to filter results
            size: Number of results to return (1-500, default: 25)
            format: Output format (json, tsv, fasta, xml)
            
        Returns:
            Search results in the requested format
        """
        search_query = query
        if organism:
            search_query += f' AND organism_name:"{organism}"'
        
        params = {
            'query': search_query,
            'format': format,
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        
        if format == 'json':
            return response.json()
        else:
            return response.text
    
    def get_protein_info(self, accession: str, format: str = 'json') -> Any:
        """
        Get detailed information for a specific protein.
        
        Args:
            accession: UniProt accession number (e.g., P04637)
            format: Output format (json, tsv, fasta, xml)
            
        Returns:
            Protein information in the requested format
        """
        params = {'format': format}
        response = self._make_request('GET', f'/uniprotkb/{accession}', params=params)
        
        if format == 'json':
            return response.json()
        else:
            return response.text
    
    def search_by_gene(
        self,
        gene: str,
        organism: Optional[str] = None,
        size: int = 25
    ) -> Dict[str, Any]:
        """
        Search for proteins by gene name or symbol.
        
        Args:
            gene: Gene name or symbol (e.g., BRCA1, INS)
            organism: Organism name or taxonomy ID to filter results
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Search results as JSON
        """
        query = f'gene:"{gene}"'
        if organism:
            query += f' AND organism_name:"{organism}"'
        
        params = {
            'query': query,
            'format': 'json',
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        return response.json()
    
    def get_protein_sequence(self, accession: str, format: str = 'fasta') -> str:
        """
        Get the amino acid sequence for a protein.
        
        Args:
            accession: UniProt accession number
            format: Output format (fasta or json)
            
        Returns:
            Protein sequence in the requested format
        """
        params = {'format': format}
        response = self._make_request('GET', f'/uniprotkb/{accession}', params=params)
        
        if format == 'json':
            return response.json()
        else:
            return response.text
    
    def search_by_function(
        self,
        go_term: Optional[str] = None,
        function: Optional[str] = None,
        organism: Optional[str] = None,
        size: int = 25
    ) -> Dict[str, Any]:
        """
        Search proteins by GO terms or functional annotations.
        
        Args:
            go_term: Gene Ontology term (e.g., GO:0005524)
            function: Functional description or keyword
            organism: Organism name or taxonomy ID to filter results
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Search results as JSON
        """
        query = 'reviewed:true'
        
        if go_term:
            query += f' AND go:"{go_term}"'
        
        if function:
            query += f' AND (cc_function:"{function}" OR ft_act_site:"{function}")'
        
        if organism:
            query += f' AND organism_name:"{organism}"'
        
        params = {
            'query': query,
            'format': 'json',
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        return response.json()
    
    def search_by_localization(
        self,
        localization: str,
        organism: Optional[str] = None,
        size: int = 25
    ) -> Dict[str, Any]:
        """
        Find proteins by subcellular localization.
        
        Args:
            localization: Subcellular localization (e.g., nucleus, mitochondria)
            organism: Organism name or taxonomy ID to filter results
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Search results as JSON
        """
        query = f'reviewed:true AND cc_subcellular_location:"{localization}"'
        
        if organism:
            query += f' AND organism_name:"{organism}"'
        
        params = {
            'query': query,
            'format': 'json',
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        return response.json()
    
    def advanced_search(
        self,
        query: Optional[str] = None,
        organism: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_mass: Optional[int] = None,
        max_mass: Optional[int] = None,
        keywords: Optional[List[str]] = None,
        size: int = 25
    ) -> Dict[str, Any]:
        """
        Complex queries with multiple filters.
        
        Args:
            query: Base search query
            organism: Organism name or taxonomy ID
            min_length: Minimum sequence length
            max_length: Maximum sequence length
            min_mass: Minimum molecular mass (Da)
            max_mass: Maximum molecular mass (Da)
            keywords: List of keywords to include
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Search results as JSON
        """
        search_query = 'reviewed:true'
        
        if query:
            search_query += f' AND ({query})'
        
        if organism:
            search_query += f' AND organism_name:"{organism}"'
        
        if min_length or max_length:
            if min_length and max_length:
                search_query += f' AND length:[{min_length} TO {max_length}]'
            elif min_length:
                search_query += f' AND length:[{min_length} TO *]'
            elif max_length:
                search_query += f' AND length:[* TO {max_length}]'
        
        if min_mass or max_mass:
            if min_mass and max_mass:
                search_query += f' AND mass:[{min_mass} TO {max_mass}]'
            elif min_mass:
                search_query += f' AND mass:[{min_mass} TO *]'
            elif max_mass:
                search_query += f' AND mass:[* TO {max_mass}]'
        
        if keywords:
            for keyword in keywords:
                search_query += f' AND keyword:"{keyword}"'
        
        params = {
            'query': search_query,
            'format': 'json',
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        return response.json()
    
    def search_by_taxonomy(
        self,
        taxonomy_id: Optional[int] = None,
        taxonomy_name: Optional[str] = None,
        size: int = 25
    ) -> Dict[str, Any]:
        """
        Search by detailed taxonomic classification.
        
        Args:
            taxonomy_id: NCBI taxonomy ID
            taxonomy_name: Taxonomic name (e.g., Mammalia, Bacteria)
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Search results as JSON
        """
        query = 'reviewed:true'
        
        if taxonomy_id:
            query += f' AND taxonomy_id:"{taxonomy_id}"'
        
        if taxonomy_name:
            query += f' AND taxonomy_name:"{taxonomy_name}"'
        
        params = {
            'query': query,
            'format': 'json',
            'size': min(size, 500)
        }
        
        response = self._make_request('GET', '/uniprotkb/search', params=params)
        return response.json()
    
    def batch_protein_lookup(
        self,
        accessions: List[str],
        format: str = 'json'
    ) -> List[Dict[str, Any]]:
        """
        Process multiple accessions efficiently.
        
        Args:
            accessions: List of UniProt accession numbers (1-100)
            format: Output format (json, tsv, fasta)
            
        Returns:
            List of results for each accession
        """
        results = []
        
        # Process in chunks to avoid overwhelming the API
        chunk_size = 10
        for i in range(0, len(accessions), chunk_size):
            chunk = accessions[i:i + chunk_size]
            
            for accession in chunk:
                try:
                    data = self.get_protein_info(accession, format=format)
                    results.append({
                        'accession': accession,
                        'data': data,
                        'success': True
                    })
                except Exception as e:
                    results.append({
                        'accession': accession,
                        'error': str(e),
                        'success': False
                    })
            
            # Small delay between chunks to be respectful to the API
            if i + chunk_size < len(accessions):
                time.sleep(0.5)
        
        return results
    
    def validate_accession(self, accession: str) -> Dict[str, Any]:
        """
        Check if an accession number is valid.
        
        Args:
            accession: UniProt accession number to validate
            
        Returns:
            Validation result with details
        """
        try:
            data = self.get_protein_info(accession, format='json')
            return {
                'accession': accession,
                'isValid': True,
                'entryType': data.get('entryType'),
                'primaryAccession': data.get('primaryAccession'),
                'exists': True
            }
        except Exception as e:
            return {
                'accession': accession,
                'isValid': False,
                'exists': False,
                'error': str(e)
            }

