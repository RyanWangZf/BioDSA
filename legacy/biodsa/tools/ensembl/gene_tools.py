"""
Ensembl Gene Tools

High-level functions for gene and transcript operations.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import EnsemblClient


def lookup_gene(
    gene_id: str,
    species: Optional[str] = None,
    expand: bool = False,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get detailed gene information by stable ID or symbol.
    
    Args:
        gene_id: Ensembl gene ID or gene symbol (e.g., ENSG00000139618, BRCA2)
        species: Species name (default: homo_sapiens)
        expand: Include transcript and exon details
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with gene information
        
    Example:
        >>> gene = lookup_gene("ENSG00000139618")
        >>> print(f"Gene: {gene['display_name']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.lookup_gene(gene_id, species=species, expand=expand)
    except Exception as e:
        raise Exception(f"Error looking up gene: {str(e)}")


def get_transcripts(
    gene_id: str,
    species: Optional[str] = None,
    canonical_only: bool = False,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get all transcripts for a gene with detailed structure.
    
    Args:
        gene_id: Ensembl gene ID
        species: Species name (default: homo_sapiens)
        canonical_only: Return only canonical transcript
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with transcript information
        
    Example:
        >>> transcripts = get_transcripts("ENSG00000139618")
        >>> print(f"Transcripts: {transcripts['transcript_count']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_transcripts(gene_id, species=species, canonical_only=canonical_only)
    except Exception as e:
        raise Exception(f"Error getting transcripts: {str(e)}")


def search_genes(
    query: str,
    species: Optional[str] = None,
    feature: str = 'gene',
    biotype: Optional[str] = None,
    limit: int = 25,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Search for genes by name, description, or identifier.
    
    Args:
        query: Search term (gene name, description, or partial match)
        species: Species name (default: homo_sapiens)
        feature: Feature type to search (gene or transcript)
        biotype: Filter by biotype (e.g., protein_coding, lncRNA)
        limit: Maximum results (1-200, default: 25)
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_genes("BRCA", limit=10)
        >>> print(df[['id', 'display_name', 'biotype']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        data = client.search_genes(
            query,
            species=species,
            feature=feature,
            biotype=biotype,
            limit=limit
        )
        
        if not data or 'results' not in data:
            return pd.DataFrame()
        
        results = []
        for entry in data['results']:
            results.append({
                'id': entry.get('id', ''),
                'display_name': entry.get('display_name', ''),
                'species': entry.get('species', ''),
                'biotype': entry.get('biotype', ''),
                'description': entry.get('description', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching genes: {str(e)}")


def get_gene_by_symbol(
    symbol: str,
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get gene information by gene symbol.
    
    Args:
        symbol: Gene symbol (e.g., BRCA2, TP53)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with gene information
        
    Example:
        >>> gene = get_gene_by_symbol("TP53")
        >>> print(f"Gene ID: {gene['id']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        species = client.get_default_species(species)
        response = client._make_request('GET', f'/lookup/symbol/{species}/{symbol}')
        return response.json()
    except Exception as e:
        raise Exception(f"Error getting gene by symbol: {str(e)}")


def batch_gene_lookup(
    gene_ids: List[str],
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Look up multiple genes simultaneously.
    
    Args:
        gene_ids: List of gene IDs (max 200)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with batch lookup results
        
    Example:
        >>> genes = batch_gene_lookup(["ENSG00000139618", "ENSG00000141510"])
        >>> for gene_id, gene_data in genes.items():
        >>>     print(f"{gene_id}: {gene_data.get('display_name')}")
    """
    if client is None:
        client = EnsemblClient()
    
    if len(gene_ids) < 1 or len(gene_ids) > 200:
        raise ValueError("Please provide between 1 and 200 gene IDs")
    
    try:
        return client.batch_gene_lookup(gene_ids, species=species)
    except Exception as e:
        raise Exception(f"Error in batch gene lookup: {str(e)}")

