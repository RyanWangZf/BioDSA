"""
OpenGenes API - Taxonomy Operations

High-level functions for taxonomy-related operations.
"""

from typing import Optional
import pandas as pd
from biodsa.tools.opengenes.client import OpenGenesClient


def get_model_organisms(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get list of model organisms used in aging research.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with model organisms
        
    Example:
        >>> organisms = get_model_organisms()
        >>> print(organisms[['name', 'latin_name']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_model_organisms(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for organism in response:
            record = {
                'id': organism.get('id'),
                'name': organism.get('name'),
                'latin_name': organism.get('latinName'),
                'description': organism.get('description', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting model organisms: {str(e)}")


def get_phylums(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get list of phylums.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with phylums
        
    Example:
        >>> phylums = get_phylums()
        >>> print(phylums[['name']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_phylums(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for phylum in response:
            record = {
                'id': phylum.get('id'),
                'name': phylum.get('name'),
                'description': phylum.get('description', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting phylums: {str(e)}")

