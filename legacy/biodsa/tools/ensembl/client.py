"""
Ensembl API Client

This module provides a client for interacting with the Ensembl REST API.
Ensembl is a comprehensive genomic database with information on genes, 
transcripts, variants, and comparative genomics.

API Documentation: https://rest.ensembl.org
"""

import requests
from typing import Dict, Any, Optional, List
import time


class EnsemblClient:
    """Client for the Ensembl REST API."""
    
    def __init__(self, base_url: str = "https://rest.ensembl.org", timeout: int = 30):
        """
        Initialize the Ensembl API client.
        
        Args:
            base_url: Base URL for the Ensembl API (default: https://rest.ensembl.org)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-Ensembl-Client/1.0.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the Ensembl API.
        
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
            raise requests.exceptions.RequestException(f"Ensembl API request failed: {str(e)}")
    
    def get_default_species(self, species: Optional[str] = None) -> str:
        """Get default species if none provided."""
        return species or 'homo_sapiens'
    
    def format_genomic_region(self, region: str) -> str:
        """
        Format genomic region string.
        
        Supports formats like: chr1:1000-2000, 1:1000-2000, ENSG00000139618
        """
        if ':' in region and '-' in region:
            return region
        elif region.startswith('ENS'):
            return region
        else:
            return region
    
    # Gene & Transcript Information
    
    def lookup_gene(
        self,
        gene_id: str,
        species: Optional[str] = None,
        expand: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed gene information by stable ID or symbol.
        
        Args:
            gene_id: Ensembl gene ID or gene symbol
            species: Species name (default: homo_sapiens)
            expand: Include transcript and exon details
            
        Returns:
            Gene information as JSON
        """
        species = self.get_default_species(species)
        params = {'species': species}
        
        if expand:
            params['expand'] = 1
        
        response = self._make_request('GET', f'/lookup/id/{gene_id}', params=params)
        return response.json()
    
    def get_transcripts(
        self,
        gene_id: str,
        species: Optional[str] = None,
        canonical_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get all transcripts for a gene.
        
        Args:
            gene_id: Ensembl gene ID
            species: Species name (default: homo_sapiens)
            canonical_only: Return only canonical transcript
            
        Returns:
            Transcript information as JSON
        """
        species = self.get_default_species(species)
        response = self._make_request(
            'GET',
            f'/lookup/id/{gene_id}',
            params={'species': species, 'expand': 1}
        )
        
        gene = response.json()
        transcripts = gene.get('Transcript', [])
        
        if canonical_only:
            transcripts = [t for t in transcripts if t.get('is_canonical') == 1]
        
        return {
            'gene_id': gene.get('id'),
            'gene_name': gene.get('display_name'),
            'transcript_count': len(transcripts),
            'transcripts': transcripts
        }
    
    def search_genes(
        self,
        query: str,
        species: Optional[str] = None,
        feature: str = 'gene',
        biotype: Optional[str] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Search for genes by name, description, or identifier.
        
        Note: This uses the lookup/symbol endpoint for gene symbol search.
        For more complex searches, use the overlap endpoints.
        
        Args:
            query: Gene symbol to search
            species: Species name (default: homo_sapiens)
            feature: Feature type (gene or transcript) - currently unused
            biotype: Filter by biotype - currently unused
            limit: Maximum results (1-200) - currently unused
            
        Returns:
            Search results as JSON (single gene if found)
        """
        species = self.get_default_species(species)
        
        # Try symbol lookup first
        try:
            response = self._make_request('GET', f'/lookup/symbol/{species}/{query}')
            gene = response.json()
            # Return in a format similar to search results
            return {'results': [gene]}
        except:
            # If symbol lookup fails, return empty results
            return {'results': []}
    
    # Sequence Data
    
    def get_sequence(
        self,
        region: str,
        species: Optional[str] = None,
        mask: Optional[str] = None,
        multiple_sequences: bool = False
    ) -> Any:
        """
        Get DNA sequence for genomic coordinates or gene/transcript ID.
        
        Args:
            region: Genomic region (chr:start-end) or feature ID
            species: Species name (default: homo_sapiens)
            mask: Repeat masking type (hard or soft)
            multiple_sequences: Return multiple sequences if applicable
            
        Returns:
            Sequence data
        """
        species = self.get_default_species(species)
        params = {}
        
        if region.startswith('ENS'):
            # Feature ID
            endpoint = f'/sequence/id/{region}'
            params['type'] = 'genomic'
        else:
            # Genomic region
            endpoint = f'/sequence/region/{species}/{region}'
        
        if mask:
            params['mask'] = mask
        
        if multiple_sequences:
            params['multiple_sequences'] = 1
        
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def get_cds_sequence(
        self,
        transcript_id: str,
        species: Optional[str] = None
    ) -> Any:
        """
        Get coding sequence (CDS) for a transcript.
        
        Args:
            transcript_id: Ensembl transcript ID
            species: Species name (default: homo_sapiens)
            
        Returns:
            CDS sequence data
        """
        species = self.get_default_species(species)
        response = self._make_request(
            'GET',
            f'/sequence/id/{transcript_id}',
            params={'type': 'cds', 'species': species}
        )
        return response.json()
    
    # Comparative Genomics
    
    def get_homologs(
        self,
        gene_id: str,
        species: Optional[str] = None,
        target_species: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find orthologous and paralogous genes across species.
        
        Args:
            gene_id: Ensembl gene ID
            species: Source species name (default: homo_sapiens)
            target_species: Target species to search
            
        Returns:
            Homolog information
        """
        species = self.get_default_species(species)
        
        # Get gene information first
        gene = self.lookup_gene(gene_id, species=species)
        
        # Try to find ortholog in target species
        target_species = target_species or 'mus_musculus'
        
        try:
            ortholog = self._make_request(
                'GET',
                f'/lookup/symbol/{target_species}/{gene["display_name"]}'
            ).json()
            
            return {
                'source_gene': {
                    'id': gene.get('id'),
                    'symbol': gene.get('display_name'),
                    'species': species,
                    'description': gene.get('description'),
                    'location': f"{gene.get('seq_region_name')}:{gene.get('start')}-{gene.get('end')}",
                    'biotype': gene.get('biotype')
                },
                'ortholog': {
                    'id': ortholog.get('id'),
                    'symbol': ortholog.get('display_name'),
                    'species': target_species,
                    'description': ortholog.get('description'),
                    'location': f"{ortholog.get('seq_region_name')}:{ortholog.get('start')}-{ortholog.get('end')}",
                    'biotype': ortholog.get('biotype')
                },
                'analysis': {
                    'method': 'Gene symbol ortholog lookup',
                    'conservation': 'Symbol-based orthology'
                }
            }
        except:
            return {
                'source_gene': {
                    'id': gene.get('id'),
                    'symbol': gene.get('display_name'),
                    'species': species,
                    'description': gene.get('description'),
                    'location': f"{gene.get('seq_region_name')}:{gene.get('start')}-{gene.get('end')}",
                    'biotype': gene.get('biotype')
                },
                'ortholog_search': {
                    'target_species': target_species,
                    'result': 'No ortholog found with same gene symbol'
                }
            }
    
    def get_gene_tree(
        self,
        gene_id: str,
        clusterset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get phylogenetic tree for gene family.
        
        Args:
            gene_id: Ensembl gene ID
            clusterset_id: Specific clusterset ID
            
        Returns:
            Gene tree data
        """
        params = {}
        if clusterset_id:
            params['clusterset_id'] = clusterset_id
        
        response = self._make_request('GET', f'/genetree/id/{gene_id}', params=params)
        return response.json()
    
    # Variant Data
    
    def get_variants(
        self,
        region: str,
        species: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get genetic variants in a genomic region.
        
        Args:
            region: Genomic region (chr:start-end)
            species: Species name (default: homo_sapiens)
            
        Returns:
            List of variants
        """
        species = self.get_default_species(species)
        
        try:
            response = self._make_request(
                'GET',
                f'/overlap/region/{species}/{region}',
                params={'feature': 'variation'}
            )
            return response.json()
        except:
            # Fallback to variation endpoint
            response = self._make_request(
                'GET',
                f'/variation/region/{species}/{region}'
            )
            return response.json()
    
    # Cross-References & Annotations
    
    def get_xrefs(
        self,
        gene_id: str,
        species: Optional[str] = None,
        external_db: Optional[str] = None,
        all_levels: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get external database cross-references.
        
        Args:
            gene_id: Ensembl gene ID
            species: Species name (default: homo_sapiens)
            external_db: Specific external database
            all_levels: Include transcript and translation xrefs
            
        Returns:
            List of cross-references
        """
        species = self.get_default_species(species)
        params = {'species': species}
        
        if external_db:
            params['external_db'] = external_db
        
        if all_levels:
            params['all_levels'] = 1
        
        response = self._make_request('GET', f'/xrefs/id/{gene_id}', params=params)
        return response.json()
    
    # Species & Assembly Information
    
    def list_species(self, division: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of available species and assemblies.
        
        Args:
            division: Ensembl division (e.g., vertebrates, plants)
            
        Returns:
            Species information
        """
        params = {}
        if division:
            params['division'] = division
        
        response = self._make_request('GET', '/info/species', params=params)
        return response.json()
    
    def get_assembly_info(
        self,
        species: Optional[str] = None,
        bands: bool = False
    ) -> Dict[str, Any]:
        """
        Get genome assembly information and statistics.
        
        Args:
            species: Species name (default: homo_sapiens)
            bands: Include chromosome banding patterns
            
        Returns:
            Assembly information
        """
        species = self.get_default_species(species)
        params = {}
        
        if bands:
            params['bands'] = 1
        
        response = self._make_request('GET', f'/info/assembly/{species}', params=params)
        return response.json()
    
    # Batch Processing
    
    def batch_gene_lookup(
        self,
        gene_ids: List[str],
        species: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Look up multiple genes simultaneously.
        
        Args:
            gene_ids: List of gene IDs (max 200)
            species: Species name (default: homo_sapiens)
            
        Returns:
            Batch lookup results
        """
        species = self.get_default_species(species)
        gene_data = {'ids': gene_ids}
        
        response = self._make_request(
            'POST',
            '/lookup/id',
            json=gene_data,
            params={'species': species}
        )
        return response.json()

