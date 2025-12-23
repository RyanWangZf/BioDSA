"""
OpenGenes API Client

This module provides a Python client for the OpenGenes API.
OpenGenes is a database of human genes associated with aging and longevity.
API Documentation: https://open-genes.com/
"""

from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class OpenGenesClient:
    """Client for interacting with OpenGenes API."""
    
    def __init__(
        self,
        base_url: str = "https://open-genes.com/api",
        timeout: int = 30
    ):
        """
        Initialize the OpenGenes API client.
        
        Args:
            base_url: Base URL for the OpenGenes API
            timeout: Request timeout in seconds
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
            'User-Agent': 'BioDSA-OpenGenes-Client/1.0.0',
            'Accept': 'application/json',
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Make an HTTP request to the OpenGenes API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary or list
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenGenes API request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Any]]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Any]]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, data=data)
    
    # Gene Operations
    
    def search_genes(
        self,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20,
        sort_order: Optional[str] = None,
        sort_by: Optional[str] = None,
        by_diseases: Optional[str] = None,
        by_disease_categories: Optional[str] = None,
        by_age_related_process: Optional[str] = None,
        by_expression_change: Optional[str] = None,
        by_selection_criteria: Optional[str] = None,
        by_aging_mechanism: Optional[str] = None,
        by_protein_class: Optional[str] = None,
        by_species: Optional[str] = None,
        by_origin: Optional[str] = None,
        by_gene_symbol: Optional[str] = None,
        confidence_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for genes with multiple filter parameters.
        
        Args:
            lang: Language (en or ru)
            page: Page number
            page_size: Page size
            sort_order: Sort order (ASC or DESC)
            sort_by: Field to sort by
            by_diseases: Filter by diseases
            by_disease_categories: Filter by disease categories
            by_age_related_process: Filter by age-related process
            by_expression_change: Filter by expression change
            by_selection_criteria: Filter by selection criteria
            by_aging_mechanism: Filter by aging mechanism
            by_protein_class: Filter by protein class
            by_species: Filter by species
            by_origin: Filter by origin
            by_gene_symbol: Filter by gene symbol
            confidence_level: Filter by confidence level
            
        Returns:
            Search results with genes
        """
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        
        if sort_order:
            params['sortOrder'] = sort_order
        if sort_by:
            params['sortBy'] = sort_by
        if by_diseases:
            params['byDiseases'] = by_diseases
        if by_disease_categories:
            params['byDiseaseCategories'] = by_disease_categories
        if by_age_related_process:
            params['byAgeRelatedProcess'] = by_age_related_process
        if by_expression_change:
            params['byExpressionChange'] = by_expression_change
        if by_selection_criteria:
            params['bySelectionCriteria'] = by_selection_criteria
        if by_aging_mechanism:
            params['byAgingMechanism'] = by_aging_mechanism
        if by_protein_class:
            params['byProteinClass'] = by_protein_class
        if by_species:
            params['bySpecies'] = by_species
        if by_origin:
            params['byOrigin'] = by_origin
        if by_gene_symbol:
            params['byGeneSymbol'] = by_gene_symbol
        if confidence_level:
            params['confidenceLevel'] = confidence_level
        
        return self.get('/gene/search', params=params)
    
    def get_gene_by_id(self, gene_id: str, lang: str = 'en') -> Dict[str, Any]:
        """Get a specific gene by its ID."""
        return self.get(f'/gene/{gene_id}', params={'lang': lang})
    
    def get_gene_by_symbol(self, symbol: str, lang: str = 'en') -> Dict[str, Any]:
        """Get a gene by its symbol."""
        return self.get(f'/gene/{symbol}', params={'lang': lang})
    
    def get_gene_by_ncbi_id(self, ncbi_id: str, lang: str = 'en') -> Dict[str, Any]:
        """Get a gene by its NCBI ID."""
        return self.get(f'/gene/ncbi/{ncbi_id}', params={'lang': lang})
    
    def get_gene_suggestions(self, lang: str = 'en') -> List[str]:
        """Get gene name suggestions."""
        return self.get('/gene/suggestions', params={'lang': lang})
    
    def get_gene_symbols(self, lang: str = 'en') -> List[str]:
        """Get all gene symbols."""
        return self.get('/gene/symbols', params={'lang': lang})
    
    def get_latest_genes(
        self,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get recently added genes."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get('/gene/by-latest', params=params)
    
    def get_genes_by_functional_cluster(
        self,
        ids: str,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get genes by functional cluster IDs."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get(f'/gene/by-functional_cluster/{ids}', params=params)
    
    def get_genes_by_selection_criteria(
        self,
        ids: str,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get genes by selection criteria IDs."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get(f'/gene/by-selection-criteria/{ids}', params=params)
    
    def get_genes_by_go_term(
        self,
        term: str,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get genes by GO term."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get(f'/gene/by-go-term/{term}', params=params)
    
    def get_genes_by_expression_change(
        self,
        expression_change: str,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get genes by expression change."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get(f'/gene/by-expression-change/{expression_change}', params=params)
    
    def get_gene_taxon(self, lang: str = 'en') -> Dict[str, Any]:
        """Get gene taxon information."""
        return self.get('/gene/taxon', params={'lang': lang})
    
    def get_genes_increase_lifespan(
        self,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get genes that increase lifespan."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get('/gene/increase-lifespan', params=params)
    
    # Taxonomy Operations
    
    def get_model_organisms(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get list of model organisms."""
        return self.get('/model-organism', params={'lang': lang})
    
    def get_phylums(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get list of phylums."""
        return self.get('/phylum', params={'lang': lang})
    
    # Protein Operations
    
    def get_protein_classes(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get protein class information."""
        return self.get('/protein-class', params={'lang': lang})
    
    # Disease Operations
    
    def get_diseases(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get disease list."""
        return self.get('/disease', params={'lang': lang})
    
    def get_disease_categories(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get disease category list."""
        return self.get('/disease-category', params={'lang': lang})
    
    # Research Operations
    
    def get_calorie_experiments(
        self,
        lang: str = 'en',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search calorie restriction experiments."""
        params = {
            'lang': lang,
            'page': page,
            'pageSize': page_size
        }
        return self.get('/diet', params=params)
    
    def get_aging_mechanisms(self, lang: str = 'en') -> List[Dict[str, Any]]:
        """Get aging mechanisms."""
        return self.get('/aging-mechanisms', params={'lang': lang})

