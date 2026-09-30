"""
NCBI Datasets API Client

This module provides a Python client for the NCBI Datasets API.
API Documentation: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/
"""

import os
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NCBIDatasetsClient:
    """Client for interacting with NCBI Datasets API."""
    
    def __init__(
        self,
        base_url: str = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the NCBI Datasets API client.
        
        Args:
            base_url: Base URL for the NCBI Datasets API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.environ.get('NCBI_API_KEY')
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
            'User-Agent': 'BioDSA-NCBI-Client/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        
        if self.api_key:
            self.session.headers['api-key'] = self.api_key
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the NCBI Datasets API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
            
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
            raise Exception(f"NCBI API request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, data=data)
    
    # Genome Operations
    
    def search_genomes(
        self,
        tax_id: int,
        assembly_level: Optional[str] = None,
        assembly_source: Optional[str] = None,
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search genome assemblies by taxonomy ID.
        
        Args:
            tax_id: NCBI taxonomy ID
            assembly_level: Filter by assembly level (complete, chromosome, scaffold, contig)
            assembly_source: Filter by source (refseq, genbank, all)
            max_results: Maximum number of results (1-1000)
            page_token: Pagination token
            
        Returns:
            Search results with genome assemblies
        """
        params = {'limit': max_results}
        
        if assembly_level:
            params['assembly_level'] = assembly_level
        if assembly_source and assembly_source != 'all':
            params['assembly_source'] = assembly_source
        if page_token:
            params['page_token'] = page_token
        
        return self.get(f'/genome/taxon/{tax_id}/dataset_report', params=params)
    
    def get_genome_info(
        self,
        accession: str,
        include_annotation: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific genome assembly.
        
        Args:
            accession: Genome assembly accession (e.g., GCF_000001405.40)
            include_annotation: Include annotation information
            
        Returns:
            Genome information
        """
        params = {}
        if include_annotation:
            params['include_annotation_type'] = 'GENOME_GFF,GENOME_GBFF'
        
        return self.get(f'/genome/accession/{accession}/dataset_report', params=params)
    
    # Gene Operations
    
    def search_genes(
        self,
        gene_symbol: Optional[str] = None,
        gene_id: Optional[int] = None,
        organism: Optional[str] = None,
        tax_id: Optional[int] = None,
        chromosome: Optional[str] = None,
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search genes by various criteria.
        
        Args:
            gene_symbol: Gene symbol (e.g., BRCA1, TP53)
            gene_id: NCBI Gene ID
            organism: Organism name
            tax_id: NCBI taxonomy ID
            chromosome: Chromosome name (not used in v2alpha)
            max_results: Maximum number of results (1-1000, not used in v2alpha)
            page_token: Pagination token (not used in v2alpha)
            
        Returns:
            Search results with gene information
        """
        # NCBI Datasets API v2alpha requires specific gene symbol + tax_id
        # or gene_id for gene lookups
        if gene_symbol and tax_id:
            return self.get(f'/gene/symbol/{gene_symbol}/taxon/{tax_id}')
        elif gene_symbol and not tax_id:
            # Default to human if no tax_id provided
            return self.get(f'/gene/symbol/{gene_symbol}/taxon/9606')
        else:
            raise ValueError("Gene symbol is required for gene search (with optional tax_id)")
    
    def get_gene_info(
        self,
        gene_id: int,
        include_sequences: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific gene.
        
        Args:
            gene_id: NCBI Gene ID
            include_sequences: Include gene sequences
            
        Returns:
            Gene information
        """
        params = {}
        if include_sequences:
            params['returned_content'] = 'COMPLETE'
        
        return self.get(f'/gene/id/{gene_id}', params=params)
    
    def get_gene_sequences(
        self,
        gene_id: int,
        sequence_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve sequences for a specific gene.
        
        Args:
            gene_id: NCBI Gene ID
            sequence_type: Type of sequence (genomic, transcript, protein, all)
            
        Returns:
            Gene sequences
        """
        params = {'returned_content': 'COMPLETE'}
        
        if sequence_type:
            if sequence_type == 'genomic':
                params['include_annotation_type'] = 'GENOME_FASTA'
            elif sequence_type == 'transcript':
                params['include_annotation_type'] = 'RNA_FASTA'
            elif sequence_type == 'protein':
                params['include_annotation_type'] = 'PROT_FASTA'
        
        return self.get(f'/gene/id/{gene_id}', params=params)
    
    # Taxonomy Operations
    
    def search_taxonomy(
        self,
        query: str,
        rank: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Search taxonomic information by organism name or keywords.
        Note: NCBI Datasets API v2alpha does not have a general taxonomy search.
        This method will attempt to look up a known tax_id.
        
        Args:
            query: Search query (should be a tax_id)
            rank: Taxonomic rank filter (not used in v2alpha)
            max_results: Maximum number of results (not used in v2alpha)
            
        Returns:
            Search results with taxonomic information
        """
        # v2alpha doesn't have a general taxonomy search endpoint
        # Try to interpret query as tax_id
        try:
            tax_id = int(query)
            return self.get_taxonomy_info(tax_id=tax_id)
        except ValueError:
            raise ValueError(
                "NCBI Datasets API v2alpha does not support taxonomy search by name. "
                "Please provide a specific taxonomy ID."
            )
    
    def get_taxonomy_info(
        self,
        tax_id: int,
        include_lineage: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed taxonomic information for a specific taxon.
        Note: This returns genome data for the taxon, as v2alpha focuses on genome data.
        
        Args:
            tax_id: NCBI taxonomy ID
            include_lineage: Include full taxonomic lineage (not used in v2alpha)
            
        Returns:
            Taxonomic information from genome dataset reports
        """
        # v2alpha doesn't have a dedicated taxonomy endpoint
        # Use genome endpoint which includes organism information
        return self.get(f'/genome/taxon/{tax_id}/dataset_report', params={'limit': 1})
    
    def get_taxonomic_lineage(
        self,
        tax_id: int,
        include_ranks: bool = True,
        include_synonyms: bool = False,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Get complete taxonomic lineage for an organism.
        Note: v2alpha returns limited taxonomy info through genome endpoint.
        
        Args:
            tax_id: NCBI taxonomy ID
            include_ranks: Include taxonomic ranks (not used in v2alpha)
            include_synonyms: Include synonyms (not used in v2alpha)
            format: Output format (only json supported in v2alpha)
            
        Returns:
            Taxonomic information from genome dataset
        """
        # v2alpha doesn't have a dedicated lineage endpoint
        # Return genome data which includes organism information
        return self.get_taxonomy_info(tax_id=tax_id)
    
    # Assembly Operations
    
    def search_assemblies(
        self,
        query: Optional[str] = None,
        assembly_level: Optional[str] = None,
        assembly_source: Optional[str] = None,
        tax_id: Optional[int] = None,
        exclude_atypical: bool = False,
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search genome assemblies with detailed filtering options.
        Note: v2alpha requires tax_id for assembly search.
        
        Args:
            query: Search query (not used in v2alpha)
            assembly_level: Assembly level filter
            assembly_source: Assembly source filter
            tax_id: NCBI taxonomy ID (required)
            exclude_atypical: Exclude atypical assemblies (not used in v2alpha)
            max_results: Maximum number of results (1-1000)
            page_token: Pagination token
            
        Returns:
            Search results with assembly information
        """
        if not tax_id:
            raise ValueError("tax_id is required for assembly search in NCBI Datasets API v2alpha")
        
        return self.search_genomes(
            tax_id=tax_id,
            assembly_level=assembly_level,
            assembly_source=assembly_source,
            max_results=max_results,
            page_token=page_token
        )
    
    def get_assembly_info(
        self,
        assembly_accession: str,
        include_annotation: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed metadata and statistics for a genome assembly.
        Note: Uses genome endpoint as assembly-specific endpoint may not be available.
        
        Args:
            assembly_accession: Assembly accession (e.g., GCF_000001405.40)
            include_annotation: Include annotation statistics
            
        Returns:
            Assembly information
        """
        # v2alpha uses genome/accession endpoint for assembly info
        return self.get_genome_info(accession=assembly_accession, include_annotation=include_annotation)
    
    def get_assembly_reports(
        self,
        assembly_accession: str,
        report_type: str = 'assembly_stats'
    ) -> Dict[str, Any]:
        """
        Get assembly quality reports and validation information.
        
        Args:
            assembly_accession: Assembly accession
            report_type: Type of report (sequence_report, assembly_stats, annotation_report)
            
        Returns:
            Assembly report
        """
        endpoint = f'/assembly/accession/{assembly_accession}'
        
        if report_type == 'sequence_report':
            endpoint += '/sequence_reports'
        elif report_type == 'assembly_stats':
            endpoint += '/dataset_report'
        elif report_type == 'annotation_report':
            endpoint += '/annotation_report'
        else:
            endpoint += '/dataset_report'
        
        return self.get(endpoint)
    
    def batch_assembly_info(
        self,
        accessions: List[str],
        include_annotation: bool = False
    ) -> Dict[str, Any]:
        """
        Get information for multiple assemblies in a single request.
        
        Args:
            accessions: List of assembly accessions (max 100)
            include_annotation: Include annotation information
            
        Returns:
            Batch assembly information
        """
        if len(accessions) > 100:
            raise ValueError("Maximum 100 accessions allowed per batch request")
        
        data = {'accessions': accessions}
        if include_annotation:
            data['include_annotation_type'] = 'GENOME_GFF,GENOME_GBFF'
        
        return self.post('/assembly/accession', data=data)
    
    def download_genome_data(
        self,
        accession: str,
        include_annotation: bool = True,
        file_format: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get download URLs and information for genome data files.
        
        Args:
            accession: Genome assembly accession
            include_annotation: Include annotation files
            file_format: File format filter (fasta, genbank, gff3, gtf, all)
            
        Returns:
            Download information
        """
        params = {}
        
        if include_annotation:
            params['include_annotation_type'] = 'GENOME_GFF,GENOME_GBFF'
        
        if file_format != 'all':
            if file_format == 'fasta':
                params['include_annotation_type'] = 'GENOME_FASTA'
            elif file_format == 'genbank':
                params['include_annotation_type'] = 'GENOME_GBFF'
            elif file_format == 'gff3':
                params['include_annotation_type'] = 'GENOME_GFF'
            elif file_format == 'gtf':
                params['include_annotation_type'] = 'GENOME_GTF'
        
        return self.get(f'/genome/accession/{accession}/download', params=params)

