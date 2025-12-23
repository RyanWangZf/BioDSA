"""
OpenGenes API - Research Operations

High-level functions for aging research-related operations.
"""

from typing import Optional
import pandas as pd
from biodsa.tools.opengenes.client import OpenGenesClient


def get_calorie_experiments(
    page: int = 1,
    page_size: int = 20,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Search calorie restriction experiments.
    
    Args:
        page: Page number
        page_size: Page size
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with calorie restriction experiments
        
    Example:
        >>> experiments = get_calorie_experiments()
        >>> print(experiments[['organism', 'diet_type', 'lifespan_change']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_calorie_experiments(lang=lang, page=page, page_size=page_size)
        
        if 'items' not in response:
            return pd.DataFrame()
        
        items = response['items']
        if not items:
            return pd.DataFrame()
        
        records = []
        for experiment in items:
            record = {
                'id': experiment.get('id'),
                'organism': experiment.get('organism'),
                'diet_type': experiment.get('dietType'),
                'lifespan_change': experiment.get('lifespanChange'),
                'reference': experiment.get('reference', ''),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting calorie experiments: {str(e)}")


def get_aging_mechanisms(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get aging mechanisms.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with aging mechanisms
        
    Example:
        >>> mechanisms = get_aging_mechanisms()
        >>> print(mechanisms[['name', 'description']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_aging_mechanisms(lang=lang)
        
        if not response:
            return pd.DataFrame()
        
        records = []
        for mechanism in response:
            record = {
                'id': mechanism.get('id'),
                'name': mechanism.get('name'),
                'description': mechanism.get('description', ''),
                'genes_count': mechanism.get('genesCount', 0),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting aging mechanisms: {str(e)}")

