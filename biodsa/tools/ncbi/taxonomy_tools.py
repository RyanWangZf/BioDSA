"""
NCBI Datasets API - Taxonomy Operations

High-level functions for taxonomy-related operations.
"""

from typing import Optional, Dict, Any
import pandas as pd
from biodsa.tools.ncbi.client import NCBIDatasetsClient


def search_taxonomy(
    query: str,
    rank: Optional[str] = None,
    max_results: int = 50,
    client: Optional[NCBIDatasetsClient] = None
) -> pd.DataFrame:
    """
    Search taxonomic information by taxonomy ID.
    Note: NCBI Datasets API v2alpha requires a specific taxonomy ID.
    
    Args:
        query: Taxonomy ID as string (e.g., '9606' for Homo sapiens)
        rank: Taxonomic rank filter (not used in v2alpha)
        max_results: Maximum number of results (not used in v2alpha)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        DataFrame with taxonomy information
        
    Example:
        >>> taxonomy = search_taxonomy('9606')  # Homo sapiens tax_id
        >>> print(taxonomy[['tax_id', 'organism_name']].head())
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.search_taxonomy(
            query=query,
            rank=rank,
            max_results=max_results
        )
        
        # Extract organism info from genome reports
        reports = response.get('reports', [])
        
        if not reports:
            return pd.DataFrame()
        
        # Extract key information
        records = []
        for report in reports:
            organism = report.get('organism', {})
            record = {
                'tax_id': organism.get('tax_id', ''),
                'organism_name': organism.get('organism_name', ''),
                'common_name': organism.get('common_name', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching taxonomy: {str(e)}")


def get_taxonomy_info(
    tax_id: int,
    include_lineage: bool = True,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get detailed taxonomic information for a specific taxon.
    Note: Returns information from genome dataset reports in v2alpha.
    
    Args:
        tax_id: NCBI taxonomy ID
        include_lineage: Include full taxonomic lineage (not used in v2alpha)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with taxonomic information
        
    Example:
        >>> info = get_taxonomy_info(9606)  # Homo sapiens
        >>> organism = info['reports'][0]['organism']
        >>> print(f"Organism: {organism['organism_name']}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.get_taxonomy_info(
            tax_id=tax_id,
            include_lineage=include_lineage
        )
        
        return response
        
    except Exception as e:
        raise Exception(f"Error getting taxonomy info: {str(e)}")


def get_organism_info(
    organism: Optional[str] = None,
    tax_id: Optional[int] = None,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get organism-specific information including available datasets.
    Note: NCBI Datasets API v2alpha requires taxonomy ID.
    
    Args:
        organism: Organism name (not supported in v2alpha, use tax_id instead)
        tax_id: NCBI taxonomy ID (required)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with organism information and available datasets
        
    Example:
        >>> info = get_organism_info(tax_id=9606)  # Homo sapiens
        >>> print(f"Available genomes: {info['genome_count']}")
    """
    if not tax_id:
        raise ValueError(
            "Taxonomy ID is required. NCBI Datasets API v2alpha does not support "
            "organism name lookup. Please provide tax_id directly."
        )
    
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        # Get organism information and available datasets
        taxonomy_response = client.get_taxonomy_info(tax_id=tax_id)
        genomes_response = client.search_genomes(tax_id=tax_id, max_results=10)
        
        return {
            'organism_info': taxonomy_response,
            'available_genomes': genomes_response.get('reports', []),
            'genome_count': genomes_response.get('total_count', 0),
        }
        
    except Exception as e:
        raise Exception(f"Error getting organism info: {str(e)}")


def get_taxonomic_lineage(
    tax_id: int,
    include_ranks: bool = True,
    include_synonyms: bool = False,
    format: str = 'json',
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get complete taxonomic lineage for an organism.
    
    Args:
        tax_id: NCBI taxonomy ID
        include_ranks: Include taxonomic ranks
        include_synonyms: Include synonyms
        format: Output format (json, text)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with taxonomic lineage
        
    Example:
        >>> lineage = get_taxonomic_lineage(9606)  # Homo sapiens
        >>> print(lineage)
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.get_taxonomic_lineage(
            tax_id=tax_id,
            include_ranks=include_ranks,
            include_synonyms=include_synonyms,
            format=format
        )
    except Exception as e:
        raise Exception(f"Error getting taxonomic lineage: {str(e)}")

