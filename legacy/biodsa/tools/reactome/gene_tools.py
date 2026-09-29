"""
Reactome API - Gene/Protein Operations

High-level functions for gene and protein-related pathway operations.
"""

from typing import Optional, Dict, Any
import pandas as pd
from biodsa.tools.reactome.client import ReactomeClient


def find_pathways_by_gene(
    gene: str,
    species: Optional[str] = None,
    client: Optional[ReactomeClient] = None
) -> Dict[str, Any]:
    """
    Find all pathways containing a specific gene or protein.
    
    Args:
        gene: Gene symbol or UniProt ID (e.g., BRCA1, P04637)
        species: Species name or taxon ID (default: Homo sapiens)
        client: Optional ReactomeClient instance
        
    Returns:
        Dictionary with gene information and associated pathways
        
    Example:
        >>> result = find_pathways_by_gene('TP53')
        >>> print(f"Found {result['pathwayCount']} pathways for {result['gene']}")
        >>> pathways_df = pd.DataFrame(result['pathways'])
    """
    if client is None:
        client = ReactomeClient()
    
    try:
        # Search for the gene/protein entity
        search_response = client.search_protein(gene_symbol=gene, species=species)
        
        # Extract protein entries from result groups
        protein_entries = []
        if search_response.get('results'):
            for group in search_response['results']:
                if group.get('typeName') == 'Protein' and group.get('entries'):
                    protein_entries.extend(group['entries'])
        
        # Filter by species if specified
        if species and protein_entries:
            protein_entries = [
                entry for entry in protein_entries
                if (isinstance(entry.get('species'), list) and
                    any(species.lower() in str(s).lower() for s in entry['species'])) or
                   (isinstance(entry.get('species'), str) and
                    species.lower() in entry['species'].lower())
            ]
        
        if not protein_entries:
            return {
                'gene': gene,
                'species': species or 'Homo sapiens',
                'message': 'No protein entity found for this gene',
                'pathways': []
            }
        
        # Get the first matching protein
        protein = protein_entries[0]
        protein_id = protein.get('stId')
        
        # Find pathways containing this protein
        # Note: This endpoint can be slow for proteins in many pathways (e.g., TP53)
        try:
            pathways_response = client.get_pathways_by_entity(protein_id)
        except Exception as e:
            # If the API call fails or times out, return limited information
            return {
                'gene': gene,
                'protein': {
                    'id': protein_id,
                    'name': protein.get('name'),
                    'species': protein.get('species', [{}])[0].get('name') if isinstance(protein.get('species'), list) else protein.get('species')
                },
                'pathwayCount': 0,
                'pathways': [],
                'error': f"Could not retrieve pathways: {str(e)}",
                'note': 'The API endpoint may be slow or unavailable for this protein. Try searching for specific pathways instead.'
            }
        
        # Format pathways
        pathways = []
        for pathway in pathways_response:
            species_data = pathway.get('species', [])
            pathway_species = None
            if species_data and len(species_data) > 0:
                pathway_species = species_data[0].get('name')
            
            pathways.append({
                'id': pathway.get('stId'),
                'name': pathway.get('name'),
                'species': pathway_species,
                'url': f"https://reactome.org/content/detail/{pathway.get('stId')}"
            })
        
        return {
            'gene': gene,
            'protein': {
                'id': protein_id,
                'name': protein.get('name'),
                'species': protein.get('species', [{}])[0].get('name') if isinstance(protein.get('species'), list) else protein.get('species')
            },
            'pathwayCount': len(pathways),
            'pathways': pathways
        }
        
    except Exception as e:
        raise Exception(f"Error finding pathways by gene: {str(e)}")


def get_gene_pathways_dataframe(
    gene: str,
    species: Optional[str] = None,
    client: Optional[ReactomeClient] = None
) -> pd.DataFrame:
    """
    Find pathways for a gene and return as DataFrame.
    
    Args:
        gene: Gene symbol or UniProt ID
        species: Species name filter
        client: Optional ReactomeClient instance
        
    Returns:
        DataFrame with pathway information
        
    Example:
        >>> pathways = get_gene_pathways_dataframe('TP53')
        >>> print(pathways[['id', 'name', 'species']].head())
    """
    result = find_pathways_by_gene(gene=gene, species=species, client=client)
    
    if not result.get('pathways'):
        return pd.DataFrame()
    
    return pd.DataFrame(result['pathways'])


def get_protein_interactions(
    pathway_id: str,
    interaction_type: str = 'all',
    client: Optional[ReactomeClient] = None
) -> Dict[str, Any]:
    """
    Get protein-protein interactions within pathways.
    
    Args:
        pathway_id: Reactome pathway stable identifier or name
        interaction_type: Type of interactions (protein-protein, regulatory, catalysis, all)
        client: Optional ReactomeClient instance
        
    Returns:
        Dictionary with interaction information
        
    Example:
        >>> interactions = get_protein_interactions('R-HSA-109581')
        >>> print(f"Found {interactions['proteinCount']} proteins")
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
        
        # Try to get participating molecules
        proteins = []
        try:
            participants = client.get_pathway_participants(resolved_id)
            proteins = [
                p for p in participants
                if p.get('schemaClass') in ['EntityWithAccessionedSequence', 'Protein']
            ]
        except Exception:
            # Extract from pathway events if participants not available
            if pathway_info.get('hasEvent'):
                proteins = [
                    event for event in pathway_info['hasEvent']
                    if 'Protein' in event.get('schemaClass', '') or
                       'Entity' in event.get('schemaClass', '')
                ][:5]
        
        # Try to get pathway reactions
        reactions = []
        try:
            events = client.get_pathway_events(resolved_id)
            reactions = [
                event for event in events
                if event.get('schemaClass') == 'Reaction'
            ]
        except Exception:
            # Extract from pathway events
            if pathway_info.get('hasEvent'):
                reactions = [
                    event for event in pathway_info['hasEvent']
                    if event.get('schemaClass') == 'Reaction'
                ][:10]
        
        # Format proteins
        formatted_proteins = []
        for protein in proteins[:20]:
            formatted_proteins.append({
                'id': protein.get('stId') or protein.get('dbId'),
                'name': protein.get('name') or protein.get('displayName'),
                'type': protein.get('schemaClass'),
                'identifier': protein.get('identifier')
            })
        
        # Format potential interactions (reactions involving proteins)
        potential_interactions = []
        for reaction in reactions[:15]:
            potential_interactions.append({
                'reactionId': reaction.get('stId') or reaction.get('dbId'),
                'reactionName': reaction.get('name') or reaction.get('displayName'),
                'type': reaction.get('schemaClass'),
                'reversible': reaction.get('reversible', False)
            })
        
        return {
            'pathwayId': resolved_id,
            'originalQuery': pathway_id,
            'basicInfo': {
                'name': pathway_info.get('displayName') or pathway_info.get('name'),
                'type': pathway_info.get('schemaClass'),
                'species': pathway_info.get('species', [{}])[0].get('displayName') if pathway_info.get('species') else None
            },
            'proteinCount': len(formatted_proteins),
            'reactionCount': len(potential_interactions),
            'proteins': formatted_proteins,
            'potentialInteractions': potential_interactions,
            'note': "Protein interactions inferred from pathway components and reactions. "
                   "For detailed molecular interactions, consider using specialized protein interaction databases.",
            'analysisNote': f"Filtered for {interaction_type} interactions" if interaction_type != 'all' else "Showing all available interaction types"
        }
        
    except Exception as e:
        raise Exception(f"Error getting protein interactions: {str(e)}")

