"""
OpenGenes API - Protein Operations

High-level functions for protein-related operations.
"""

from typing import Optional
import pandas as pd
from biodsa.tools.opengenes.client import OpenGenesClient


def get_protein_classes(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get protein class information.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with protein classes
        
    Example:
        >>> protein_classes = get_protein_classes()
        >>> print(protein_classes[['name', 'description']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_protein_classes(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for protein_class in response:
            record = {
                'id': protein_class.get('id'),
                'name': protein_class.get('name'),
                'description': protein_class.get('description', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting protein classes: {str(e)}")

