"""
Human Protein Atlas Protein Tools

High-level functions for protein search and information retrieval.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import ProteinAtlasClient


def search_proteins(
    query: str,
    columns: Optional[List[str]] = None,
    max_results: Optional[int] = 100,
    client: Optional[ProteinAtlasClient] = None
) -> pd.DataFrame:
    """
    Search for proteins by name, gene symbol, or description.
    
    Args:
        query: Search query (gene name, protein name, or keyword)
        columns: Specific columns to include in results
        max_results: Maximum number of results (default: 100)
        client: Optional ProteinAtlasClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_proteins("BRCA", max_results=10)
        >>> print(df[['Gene', 'Ensembl', 'Gene description']])
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        results = client.search_proteins(query, columns=columns, max_results=max_results)
        return pd.DataFrame(results)
    except Exception as e:
        raise Exception(f"Error searching proteins: {str(e)}")


def get_protein_info(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific protein by gene symbol.
    
    Args:
        gene: Gene symbol (e.g., BRCA1, TP53)
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with protein information
        
    Example:
        >>> info = get_protein_info("TP53")
        >>> print(f"Gene: {info.get('Gene')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_protein_info(gene)
    except Exception as e:
        raise Exception(f"Error getting protein info: {str(e)}")


def batch_protein_lookup(
    genes: List[str],
    columns: Optional[List[str]] = None,
    client: Optional[ProteinAtlasClient] = None
) -> List[Dict[str, Any]]:
    """
    Look up multiple proteins simultaneously.
    
    Args:
        genes: List of gene symbols (max 100)
        columns: Specific columns to include
        client: Optional ProteinAtlasClient instance
        
    Returns:
        List of results for each gene
        
    Example:
        >>> results = batch_protein_lookup(["TP53", "BRCA1", "BRCA2"])
        >>> for r in results:
        >>>     if r['success']:
        >>>         print(f"{r['gene']}: Found")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    if len(genes) > 100:
        raise ValueError("Maximum 100 genes allowed for batch lookup")
    
    try:
        return client.batch_protein_lookup(genes, columns=columns)
    except Exception as e:
        raise Exception(f"Error in batch protein lookup: {str(e)}")


def get_protein_classes(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get protein classification and functional annotation data.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with protein classification data
        
    Example:
        >>> classes = get_protein_classes("TP53")
        >>> print(f"Protein class: {classes.get('Protein class')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_protein_classes(gene)
    except Exception as e:
        raise Exception(f"Error getting protein classes: {str(e)}")


def advanced_search(
    query: Optional[str] = None,
    tissue_specific: Optional[str] = None,
    subcellular_location: Optional[str] = None,
    cancer_prognostic: Optional[str] = None,
    protein_class: Optional[str] = None,
    chromosome: Optional[str] = None,
    antibody_reliability: Optional[str] = None,
    columns: Optional[List[str]] = None,
    max_results: Optional[int] = 100,
    client: Optional[ProteinAtlasClient] = None
) -> pd.DataFrame:
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
        client: Optional ProteinAtlasClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = advanced_search(
        >>>     tissue_specific="liver",
        >>>     subcellular_location="nucleus",
        >>>     max_results=50
        >>> )
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        results = client.advanced_search(
            query=query,
            tissue_specific=tissue_specific,
            subcellular_location=subcellular_location,
            cancer_prognostic=cancer_prognostic,
            protein_class=protein_class,
            chromosome=chromosome,
            antibody_reliability=antibody_reliability,
            columns=columns,
            max_results=max_results
        )
        return pd.DataFrame(results)
    except Exception as e:
        raise Exception(f"Error in advanced search: {str(e)}")

