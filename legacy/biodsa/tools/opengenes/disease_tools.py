"""
OpenGenes API - Disease Operations

High-level functions for disease-related operations.
"""

from typing import Optional
import pandas as pd
from biodsa.tools.opengenes.client import OpenGenesClient


def get_diseases(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get list of diseases associated with aging genes.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with diseases
        
    Example:
        >>> diseases = get_diseases()
        >>> print(diseases[['name', 'categories']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_diseases(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for disease in response:
            record = {
                'id': disease.get('id'),
                'name': disease.get('name'),
                'icd_code': disease.get('icdCode', ''),
                'categories': ', '.join(disease.get('categories', [])) if disease.get('categories') else '',
                'description': disease.get('description', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting diseases: {str(e)}")


def get_disease_categories(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get list of disease categories.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with disease categories
        
    Example:
        >>> categories = get_disease_categories()
        >>> print(categories[['name']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_disease_categories(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for category in response:
            record = {
                'id': category.get('id'),
                'name': category.get('name'),
                'description': category.get('description', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting disease categories: {str(e)}")

