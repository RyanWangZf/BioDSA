"""
Human Protein Atlas API Client

This module provides a client for interacting with the Human Protein Atlas API.
The Human Protein Atlas is a comprehensive resource for protein expression and
localization across tissues, cells, and organs.

API Documentation: https://www.proteinatlas.org/about/help
"""

import requests
from typing import Dict, Any, Optional, List
import time


class ProteinAtlasClient:
    """Client for the Human Protein Atlas API."""
    
    def __init__(self, base_url: str = "https://www.proteinatlas.org", timeout: int = 30):
        """
        Initialize the Human Protein Atlas API client.
        
        Args:
            base_url: Base URL for the API (default: https://www.proteinatlas.org)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-ProteinAtlas-Client/1.0.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the Protein Atlas API.
        
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
            raise requests.exceptions.RequestException(f"Protein Atlas API request failed: {str(e)}")
    
    def _parse_tsv_response(self, data: str) -> List[Dict[str, Any]]:
        """
        Parse TSV response data into list of dictionaries.
        
        Args:
            data: TSV formatted data
            
        Returns:
            List of dictionaries representing rows
        """
        lines = data.strip().split('\n')
        if len(lines) < 2:
            return []
        
        headers = lines[0].split('\t')
        results = []
        
        for i in range(1, len(lines)):
            if lines[i].strip():
                values = lines[i].split('\t')
                row = {}
                for j, header in enumerate(headers):
                    row[header] = values[j] if j < len(values) else ''
                results.append(row)
        
        return results
    
    # Core Search and Retrieval Methods
    
    def search_proteins(
        self,
        query: str,
        columns: Optional[List[str]] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for proteins by name, gene symbol, or description.
        
        Args:
            query: Search query (gene name, protein name, or keyword)
            columns: Specific columns to include in results
            max_results: Maximum number of results (default: all)
            
        Returns:
            List of protein results
        """
        # Default columns: basic protein information
        default_columns = ['g', 'gs', 'eg', 'gd', 'up', 'chr', 'pc', 'pe']
        search_columns = columns if columns else default_columns
        
        params = {
            'search': query,
            'format': 'tsv',
            'columns': ','.join(search_columns),
            'compress': 'no'
        }
        
        response = self._make_request('GET', '/api/search_download.php', params=params)
        results = self._parse_tsv_response(response.text)
        
        if max_results and len(results) > max_results:
            return results[:max_results]
        
        return results
    
    def get_protein_info(self, gene: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific protein by gene symbol.
        
        Args:
            gene: Gene symbol (e.g., BRCA1, TP53)
            
        Returns:
            Dictionary with protein information
        """
        results = self.search_proteins(gene, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    # Tissue Expression Methods
    
    def get_tissue_expression(self, gene: str) -> Dict[str, Any]:
        """
        Get tissue-specific expression data for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with tissue expression data
        """
        columns = [
            'g', 'eg', 'rnats', 'rnatd', 'rnatss',
            't_RNA_adipose_tissue', 't_RNA_adrenal_gland', 't_RNA_brain',
            't_RNA_breast', 't_RNA_colon', 't_RNA_heart_muscle',
            't_RNA_kidney', 't_RNA_liver', 't_RNA_lung',
            't_RNA_ovary', 't_RNA_pancreas', 't_RNA_prostate',
            't_RNA_skeletal_muscle', 't_RNA_skin_1', 't_RNA_spleen',
            't_RNA_stomach_1', 't_RNA_testis', 't_RNA_thyroid_gland'
        ]
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    def get_blood_expression(self, gene: str) -> Dict[str, Any]:
        """
        Get blood cell expression data for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with blood expression data
        """
        columns = [
            'g', 'eg', 'rnabcs', 'rnabcd', 'rnabcss',
            'blood_RNA_basophil', 'blood_RNA_classical_monocyte',
            'blood_RNA_eosinophil', 'blood_RNA_neutrophil', 'blood_RNA_NK-cell'
        ]
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    def get_brain_expression(self, gene: str) -> Dict[str, Any]:
        """
        Get brain region expression data for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with brain expression data
        """
        columns = [
            'g', 'eg', 'rnabrs', 'rnabrd', 'rnabrss',
            'brain_RNA_amygdala', 'brain_RNA_cerebellum',
            'brain_RNA_cerebral_cortex', 'brain_RNA_hippocampal_formation',
            'brain_RNA_hypothalamus'
        ]
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    # Subcellular Localization Methods
    
    def get_subcellular_location(self, gene: str) -> Dict[str, Any]:
        """
        Get subcellular localization data for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with subcellular localization data
        """
        columns = ['g', 'eg', 'scl', 'scml', 'scal', 'relce']
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    # Pathology and Cancer Methods
    
    def get_pathology_data(self, gene: str) -> Dict[str, Any]:
        """
        Get cancer and pathology data for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with pathology data
        """
        columns = [
            'g', 'eg',
            'prognostic_Breast_Invasive_Carcinoma_(TCGA)',
            'prognostic_Colon_Adenocarcinoma_(TCGA)',
            'prognostic_Lung_Adenocarcinoma_(TCGA)',
            'prognostic_Prostate_Adenocarcinoma_(TCGA)'
        ]
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    # Antibody Information Methods
    
    def get_antibody_info(self, gene: str) -> Dict[str, Any]:
        """
        Get antibody validation and staining information for a protein.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with antibody information
        """
        columns = ['g', 'eg', 'ab', 'abrr', 'relih', 'relmb', 'relce']
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}
    
    # Advanced Search Methods
    
    def advanced_search(
        self,
        query: Optional[str] = None,
        tissue_specific: Optional[str] = None,
        subcellular_location: Optional[str] = None,
        cancer_prognostic: Optional[str] = None,
        protein_class: Optional[str] = None,
        chromosome: Optional[str] = None,
        antibody_reliability: Optional[str] = None,
        columns: Optional[List[str]] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform advanced search with multiple filters and criteria.
        
        Args:
            query: Base search query
            tissue_specific: Tissue-specific expression filter
            subcellular_location: Subcellular localization filter
            cancer_prognostic: Cancer prognostic filter
            protein_class: Protein class filter
            chromosome: Chromosome filter
            antibody_reliability: Antibody reliability filter
            columns: Specific columns to include
            max_results: Maximum number of results
            
        Returns:
            List of matching proteins
        """
        search_query = query or ''
        
        if tissue_specific:
            search_query += ('' if not search_query else ' AND ') + f'tissue:"{tissue_specific}"'
        
        if subcellular_location:
            search_query += ('' if not search_query else ' AND ') + f'location:"{subcellular_location}"'
        
        if cancer_prognostic:
            search_query += ('' if not search_query else ' AND ') + f'prognostic:"{cancer_prognostic}"'
        
        if protein_class:
            search_query += ('' if not search_query else ' AND ') + f'class:"{protein_class}"'
        
        if chromosome:
            search_query += ('' if not search_query else ' AND ') + f'chromosome:"{chromosome}"'
        
        if antibody_reliability:
            search_query += ('' if not search_query else ' AND ') + f'reliability:"{antibody_reliability}"'
        
        if not search_query:
            search_query = '*'  # Search for everything if no criteria
        
        return self.search_proteins(search_query, columns=columns, max_results=max_results)
    
    # Batch Processing Methods
    
    def batch_protein_lookup(
        self,
        genes: List[str],
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Look up multiple proteins simultaneously.
        
        Args:
            genes: List of gene symbols (max 100)
            columns: Specific columns to include
            
        Returns:
            List of results for each gene
        """
        if len(genes) > 100:
            raise ValueError("Maximum 100 genes allowed for batch lookup")
        
        results = []
        for gene in genes:
            try:
                data = self.search_proteins(gene, columns=columns, max_results=1)
                results.append({
                    'gene': gene,
                    'data': data[0] if data else {},
                    'success': bool(data)
                })
            except Exception as e:
                results.append({
                    'gene': gene,
                    'error': str(e),
                    'success': False
                })
            
            # Small delay to be respectful to the API
            if len(results) < len(genes):
                time.sleep(0.1)
        
        return results
    
    # Protein Classification Methods
    
    def get_protein_classes(self, gene: str) -> Dict[str, Any]:
        """
        Get protein classification and functional annotation data.
        
        Args:
            gene: Gene symbol
            
        Returns:
            Dictionary with protein classification data
        """
        columns = ['g', 'eg', 'pc', 'upbp', 'up_mf', 'pe']
        
        results = self.search_proteins(gene, columns=columns, max_results=1)
        
        if results:
            return results[0]
        else:
            return {}

