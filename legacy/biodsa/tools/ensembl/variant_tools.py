"""
Ensembl Variant Tools

Functions for genetic variant analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import EnsemblClient


def get_variants(
    region: str,
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Get genetic variants in a genomic region.
    
    Args:
        region: Genomic region (chr:start-end)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with variant information
        
    Example:
        >>> variants = get_variants("1:1000000-1100000")
        >>> print(variants[['id', 'start', 'end', 'allele_string']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        data = client.get_variants(region, species=species)
        
        if not data:
            return pd.DataFrame()
        
        results = []
        for variant in data:
            results.append({
                'id': variant.get('id', ''),
                'seq_region_name': variant.get('seq_region_name', ''),
                'start': variant.get('start', 0),
                'end': variant.get('end', 0),
                'strand': variant.get('strand', 0),
                'allele_string': variant.get('allele_string', ''),
                'variant_class': variant.get('variant_class', ''),
                'source': variant.get('source', ''),
                'consequence_type': variant.get('consequence_type', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error getting variants: {str(e)}")


def get_variant_info(
    variant_id: str,
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific variant.
    
    Args:
        variant_id: Variant ID (e.g., rs123456)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with variant information
        
    Example:
        >>> info = get_variant_info("rs699")
        >>> print(f"Variant: {info.get('name')}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        species = client.get_default_species(species)
        response = client._make_request('GET', f'/variation/{species}/{variant_id}')
        return response.json()
    except Exception as e:
        raise Exception(f"Error getting variant info: {str(e)}")

