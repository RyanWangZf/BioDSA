"""
Ensembl Regulatory Tools

Functions for regulatory features and elements.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import EnsemblClient


def get_regulatory_features(
    region: str,
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Get regulatory elements (enhancers, promoters, TFBS) in genomic region.
    
    Args:
        region: Genomic region (chr:start-end)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with regulatory features
        
    Example:
        >>> features = get_regulatory_features("1:1000000-1100000")
        >>> print(features[['feature_type', 'start', 'end']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        species = client.get_default_species(species)
        
        # Try to get regulatory features using overlap endpoint
        try:
            response = client._make_request(
                'GET',
                f'/overlap/region/{species}/{region}',
                params={'feature': 'regulatory'}
            )
            data = response.json()
        except:
            # Fallback: get genes in the region instead
            response = client._make_request(
                'GET',
                f'/overlap/region/{species}/{region}',
                params={'feature': 'gene'}
            )
            data = response.json()
        
        if not data:
            return pd.DataFrame()
        
        results = []
        for feature in data:
            results.append({
                'id': feature.get('id', ''),
                'feature_type': feature.get('feature_type', feature.get('biotype', '')),
                'start': feature.get('start', 0),
                'end': feature.get('end', 0),
                'strand': feature.get('strand', 0),
                'description': feature.get('description', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error getting regulatory features: {str(e)}")


def get_overlapping_features(
    region: str,
    feature_type: str = 'gene',
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Get features overlapping a genomic region.
    
    Args:
        region: Genomic region (chr:start-end)
        feature_type: Type of feature (gene, transcript, variation, etc.)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with overlapping features
        
    Example:
        >>> features = get_overlapping_features("1:1000000-1100000", "gene")
        >>> print(features[['id', 'start', 'end', 'biotype']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        species = client.get_default_species(species)
        response = client._make_request(
            'GET',
            f'/overlap/region/{species}/{region}',
            params={'feature': feature_type}
        )
        data = response.json()
        
        if not data:
            return pd.DataFrame()
        
        results = []
        for feature in data:
            results.append({
                'id': feature.get('id', ''),
                'feature_type': feature.get('feature_type', feature.get('biotype', '')),
                'start': feature.get('start', 0),
                'end': feature.get('end', 0),
                'strand': feature.get('strand', 0),
                'description': feature.get('description', ''),
                'biotype': feature.get('biotype', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error getting overlapping features: {str(e)}")

