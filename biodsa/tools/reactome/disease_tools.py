"""
Reactome API - Disease Operations

High-level functions for disease-related pathway operations.
"""

from typing import Optional
import pandas as pd
from biodsa.tools.reactome.client import ReactomeClient


def find_pathways_by_disease(
    disease: str,
    size: int = 25,
    client: Optional[ReactomeClient] = None
) -> pd.DataFrame:
    """
    Find disease-associated pathways and mechanisms.
    
    Args:
        disease: Disease name or DOID identifier
        size: Number of pathways to return (1-100)
        client: Optional ReactomeClient instance
        
    Returns:
        DataFrame with disease-associated pathways
        
    Example:
        >>> pathways = find_pathways_by_disease('cancer')
        >>> print(pathways[['id', 'name', 'species']].head())
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Search for disease-related pathways
        search_response = client.search_query(query=disease, entity_type='Pathway')
        
        # Extract pathway entries from result groups
        pathway_entries = []
        if search_response.get('results'):
            for group in search_response['results']:
                if group.get('typeName') == 'Pathway' and group.get('entries'):
                    pathway_entries.extend(group['entries'])
        
        # Limit results
        pathway_entries = pathway_entries[:size]
        
        if not pathway_entries:
            return pd.DataFrame()
        
        # Format results
        records = []
        for pathway in pathway_entries:
            # Remove HTML tags from name
            name = pathway.get('name', 'Unknown')
            if '<' in name:
                import re
                name = re.sub(r'<[^>]*>', '', name)
            
            # Extract species
            species_data = pathway.get('species', 'Unknown')
            if isinstance(species_data, list) and len(species_data) > 0:
                species = species_data[0]
            else:
                species = species_data
            
            # Truncate description
            description = pathway.get('summation', 'No description available')
            if len(description) > 200:
                description = description[:200] + '...'
            
            record = {
                'id': pathway.get('stId') or pathway.get('id'),
                'name': name,
                'type': pathway.get('exactType') or pathway.get('typeName', 'Unknown'),
                'species': species,
                'description': description,
                'url': f"https://reactome.org/content/detail/{pathway.get('stId') or pathway.get('id')}"
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error finding pathways by disease: {str(e)}")

