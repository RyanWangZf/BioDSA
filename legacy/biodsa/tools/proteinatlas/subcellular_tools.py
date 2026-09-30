"""
Human Protein Atlas Subcellular Localization Tools

Functions for subcellular localization analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import ProteinAtlasClient


def get_subcellular_location(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get subcellular localization data for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with subcellular localization data
        
    Example:
        >>> loc = get_subcellular_location("TP53")
        >>> print(f"Location: {loc.get('Subcellular location')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_subcellular_location(gene)
    except Exception as e:
        raise Exception(f"Error getting subcellular location: {str(e)}")


def search_by_subcellular_location(
    location: str,
    reliability: Optional[str] = None,
    max_results: Optional[int] = 100,
    client: Optional[ProteinAtlasClient] = None
) -> pd.DataFrame:
    """
    Find proteins localized to specific subcellular compartments.
    
    Args:
        location: Subcellular location (e.g., nucleus, mitochondria, cytosol)
        reliability: Reliability filter (approved, enhanced, supported, uncertain)
        max_results: Maximum number of results
        client: Optional ProteinAtlasClient instance
        
    Returns:
        DataFrame with proteins in the specified location
        
    Example:
        >>> df = search_by_subcellular_location("nucleus", reliability="approved")
        >>> print(df[['Gene', 'Subcellular location']])
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        search_query = f'location:"{location}"'
        if reliability:
            search_query += f' AND reliability:"{reliability}"'
        
        results = client.search_proteins(search_query, max_results=max_results)
        return pd.DataFrame(results)
    except Exception as e:
        raise Exception(f"Error searching by subcellular location: {str(e)}")

