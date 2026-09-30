"""
Reactome API - Pathway Operations

High-level functions for pathway-related operations.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from biodsa.tools.reactome.client import ReactomeClient


def search_pathways(
    query: str,
    entity_type: Optional[str] = None,
    size: int = 20,
    client: Optional[ReactomeClient] = None
) -> pd.DataFrame:
    """
    Search for biological pathways by name, description, or keywords.
    
    Args:
        query: Search query (pathway name, process, keywords)
        entity_type: Type of entity (pathway, reaction, protein, complex, disease)
        size: Number of results to return (1-100)
        client: Optional ReactomeClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> pathways = search_pathways('apoptosis')
        >>> print(pathways[['id', 'name', 'species']].head())
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        response = client.search_query(
            query=query,
            entity_type=entity_type,
            cluster=True
        )
        
        # Extract entries from all result groups
        all_entries = []
        if response.get('results'):
            for group in response['results']:
                if group.get('entries'):
                    all_entries.extend(group['entries'])
        
        # Filter by type if specified
        if entity_type:
            type_filter = entity_type.lower()
            all_entries = [
                entry for entry in all_entries
                if type_filter in entry.get('exactType', '').lower() or
                   type_filter in entry.get('typeName', '').lower()
            ]
        
        # Limit results
        all_entries = all_entries[:size]
        
        if not all_entries:
            return pd.DataFrame()
        
        # Format results
        records = []
        for item in all_entries:
            # Remove HTML tags from name
            name = item.get('name', 'Unknown')
            if '<' in name:
                import re
                name = re.sub(r'<[^>]*>', '', name)
            
            # Extract species
            species_data = item.get('species', 'Unknown')
            if isinstance(species_data, list) and len(species_data) > 0:
                species = species_data[0]
            else:
                species = species_data
            
            # Truncate description
            description = item.get('summation', 'No description available')
            if len(description) > 200:
                description = description[:200] + '...'
            
            record = {
                'id': item.get('stId') or item.get('id'),
                'name': name,
                'type': item.get('exactType') or item.get('typeName', 'Unknown'),
                'species': species,
                'description': description,
                'url': f"https://reactome.org/content/detail/{item.get('stId') or item.get('id')}"
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching pathways: {str(e)}")


def get_pathway_details(
    pathway_id: str,
    client: Optional[ReactomeClient] = None
) -> Dict[str, Any]:
    """
    Get comprehensive information about a specific pathway.
    
    Args:
        pathway_id: Reactome pathway stable identifier or name
        client: Optional ReactomeClient instance
        
    Returns:
        Dictionary with pathway details
        
    Example:
        >>> details = get_pathway_details('R-HSA-109581')
        >>> print(f"Pathway: {details['basicInfo']['displayName']}")
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Resolve pathway ID if it's a name
        resolved_id = client.resolve_pathway_id(pathway_id)
        
        if not resolved_id:
            return {
                'error': f"No pathway found for identifier: {pathway_id}",
                'suggestion': 'Try using a Reactome stable identifier (e.g., R-HSA-1640170) or search for the pathway first'
            }
        
        # Get basic pathway information
        basic_info = client.get_pathway_data(resolved_id)
        
        # Try to get additional data
        participants = None
        events = None
        
        try:
            participants = client.get_pathway_participants(resolved_id)
        except Exception:
            pass
        
        try:
            events = client.get_pathway_events(resolved_id)
        except Exception:
            pass
        
        return {
            'id': resolved_id,
            'originalQuery': pathway_id,
            'basicInfo': basic_info,
            'participants': participants if participants else 'Not available',
            'events': events if events else 'Not available',
            'url': f"https://reactome.org/content/detail/{resolved_id}",
            'diagramUrl': f"https://reactome.org/PathwayBrowser/#{resolved_id}"
        }
        
    except Exception as e:
        raise Exception(f"Error getting pathway details: {str(e)}")


def get_pathway_hierarchy(
    pathway_id: str,
    client: Optional[ReactomeClient] = None
) -> Dict[str, Any]:
    """
    Get hierarchical structure and parent/child relationships for a pathway.
    
    Args:
        pathway_id: Reactome pathway stable identifier or name
        client: Optional ReactomeClient instance
        
    Returns:
        Dictionary with hierarchy information
        
    Example:
        >>> hierarchy = get_pathway_hierarchy('R-HSA-109581')
        >>> print(f"Children: {len(hierarchy['children'])}")
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Resolve pathway ID if it's a name
        resolved_id = client.resolve_pathway_id(pathway_id)
        
        if not resolved_id:
            return {
                'error': f"No pathway found for identifier: {pathway_id}",
                'suggestion': 'Try using a Reactome stable identifier'
            }
        
        # Get pathway information
        pathway_info = client.get_pathway_data(resolved_id)
        
        # Extract child events
        children = []
        if pathway_info.get('hasEvent'):
            children = [
                {
                    'id': event.get('stId') or event.get('dbId'),
                    'name': event.get('displayName') or event.get('name'),
                    'type': event.get('schemaClass', 'Event')
                }
                for event in pathway_info['hasEvent'][:10]
            ]
        
        # Try to get orthologous pathways (related pathways)
        ancestors = client.get_orthologous_pathways(resolved_id)[:10] if resolved_id else []
        
        return {
            'pathwayId': resolved_id,
            'originalQuery': pathway_id,
            'basicInfo': {
                'name': pathway_info.get('displayName') or pathway_info.get('name'),
                'type': pathway_info.get('schemaClass'),
                'species': pathway_info.get('species', [{}])[0].get('displayName') if pathway_info.get('species') else None
            },
            'children': children if children else 'No child pathways available',
            'relatedPathways': [
                {
                    'id': ancestor.get('stId') or ancestor.get('dbId'),
                    'name': ancestor.get('displayName') or ancestor.get('name'),
                    'type': ancestor.get('schemaClass', 'Pathway')
                }
                for ancestor in ancestors
            ] if ancestors else []
        }
        
    except Exception as e:
        raise Exception(f"Error getting pathway hierarchy: {str(e)}")


def get_pathway_reactions(
    pathway_id: str,
    client: Optional[ReactomeClient] = None
) -> pd.DataFrame:
    """
    Get all biochemical reactions within a pathway.
    
    Args:
        pathway_id: Reactome pathway stable identifier or name
        client: Optional ReactomeClient instance
        
    Returns:
        DataFrame with pathway reactions
        
    Example:
        >>> reactions = get_pathway_reactions('R-HSA-109581')
        >>> print(reactions[['id', 'name', 'type']].head())
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Resolve pathway ID if it's a name
        resolved_id = client.resolve_pathway_id(pathway_id)
        
        if not resolved_id:
            return pd.DataFrame()
        
        # Get pathway events
        events = client.get_pathway_events(resolved_id)
        
        # Filter for reactions only
        reactions = [
            event for event in events
            if event.get('schemaClass') in ['Reaction', 'BlackBoxEvent']
        ]
        
        if not reactions:
            return pd.DataFrame()
        
        # Format results
        records = []
        for reaction in reactions:
            species_data = reaction.get('species', [])
            species = species_data[0].get('name') if species_data and len(species_data) > 0 else None
            
            record = {
                'id': reaction.get('stId'),
                'name': reaction.get('name'),
                'type': reaction.get('schemaClass'),
                'reversible': reaction.get('reversible', False),
                'species': species,
                'url': f"https://reactome.org/content/detail/{reaction.get('stId')}"
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting pathway reactions: {str(e)}")


def get_pathway_participants(
    pathway_id: str,
    max_results: int = 50,
    client: Optional[ReactomeClient] = None
) -> pd.DataFrame:
    """
    Get all molecules (proteins, genes, compounds) participating in a pathway.
    
    Args:
        pathway_id: Reactome pathway stable identifier or name
        max_results: Maximum number of participants to return
        client: Optional ReactomeClient instance
        
    Returns:
        DataFrame with pathway participants
        
    Example:
        >>> participants = get_pathway_participants('R-HSA-109581')
        >>> print(participants[['id', 'name', 'type']].head())
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Resolve pathway ID if it's a name
        resolved_id = client.resolve_pathway_id(pathway_id)
        
        if not resolved_id:
            return pd.DataFrame()
        
        # Get participating molecules
        participants = client.get_pathway_participants(resolved_id)
        
        if not participants:
            return pd.DataFrame()
        
        # Limit results
        participants = participants[:max_results]
        
        # Format results
        records = []
        for participant in participants:
            species_data = participant.get('species', [])
            if species_data and len(species_data) > 0:
                species = species_data[0].get('name') or species_data[0].get('displayName')
            else:
                species = None
            
            record = {
                'id': participant.get('stId'),
                'name': participant.get('name') or participant.get('displayName'),
                'type': participant.get('schemaClass'),
                'species': species,
                'identifier': participant.get('identifier'),
                'url': f"https://reactome.org/content/detail/{participant.get('stId')}"
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting pathway participants: {str(e)}")

