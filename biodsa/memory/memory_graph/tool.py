"""
Memory Graph Tool Functions

This module exposes the knowledge graph operations as synchronous callable tool functions
for use in MCP servers, APIs, or other external interfaces.
"""

import asyncio
from typing import List, Dict, Union, Optional, Any
from .graph import KnowledgeGraphManager
from .schema import Entity, Relation, KnowledgeGraph

# Global cache for KnowledgeGraphManager instances (one per cache_dir)
_manager_cache: Dict[str, KnowledgeGraphManager] = {}

def _get_manager(cache_dir: Optional[str] = None) -> KnowledgeGraphManager:
    """
    Get or create a KnowledgeGraphManager instance for the given cache directory.
    Reuses existing instances to avoid recreating managers and reloading data.
    """
    cache_key = cache_dir if cache_dir else "default"
    if cache_key not in _manager_cache:
        _manager_cache[cache_key] = KnowledgeGraphManager(cache_dir=cache_dir)
    return _manager_cache[cache_key]

def clear_manager_cache(cache_dir: Optional[str] = None):
    """
    Clear the cached manager instance for a specific cache directory or all managers.
    Useful after clearing a graph or when you want to reset the manager state.
    """
    if cache_dir:
        cache_key = cache_dir if cache_dir else "default"
        if cache_key in _manager_cache:
            del _manager_cache[cache_key]
    else:
        _manager_cache.clear()

def create_entities(
    entities: List[Dict[str, Any]], 
    context: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Create new entities in the knowledge graph.
    
    Args:
        entities: List of entity dictionaries with 'name', 'entity_type', and 'observations'
        context: Optional context for the graph (e.g., 'research', 'clinical')
    
    Returns:
        List of created entity dictionaries
    
    Example:
        entities = [
            {
                "name": "Clinical Trial NCT12345",
                "entity_type": "clinical_trial", 
                "observations": ["Phase II trial", "Diabetes treatment"]
            }
        ]
        result = create_entities(entities)
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_create_entities():
        # Convert dict inputs to Entity objects
        entity_objects = [
            Entity(
                name=e["name"],
                entity_type=e["entity_type"],
                observations=e.get("observations", [])
            )
            for e in entities
        ]
        
        # Create entities using the manager
        created_entities = await knowledge_graph_manager.create_entities(
            entity_objects, context
        )
        
        # Convert back to dictionaries
        return [entity.to_dict() for entity in created_entities]
    
    return asyncio.run(_async_create_entities())


def create_relations(
    relations: List[Dict[str, str]], 
    context: Optional[str] = None ,
    cache_dir: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Create new relations between entities in the knowledge graph.
    
    Args:
        relations: List of relation dictionaries with 'from_entity', 'to_entity', and 'relation_type'
        context: Optional context for the graph
    
    Returns:
        List of created relation dictionaries
    
    Example:
        relations = [
            {
                "from_entity": "Dr. Jane Smith",
                "to_entity": "Clinical Trial NCT12345", 
                "relation_type": "leads"
            }
        ]
        result = create_relations(relations)
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_create_relations():
        # Convert dict inputs to Relation objects
        relation_objects = [
            Relation(
                from_entity=r["from_entity"],
                to_entity=r["to_entity"],
                relation_type=r["relation_type"]
            )
            for r in relations
        ]
        
        # Create relations using the manager
        created_relations = await knowledge_graph_manager.create_relations(
            relation_objects, context
        )
        
        # Convert back to dictionaries
        return [relation.to_dict() for relation in created_relations]
    
    return asyncio.run(_async_create_relations())


def add_observations(
    observations: List[Dict[str, Union[str, List[str]]]], 
    context: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Add observations to entities. Creates new entities if they don't exist.
    
    Args:
        observations: List of observation dictionaries with 'entityName' and 'contents'
        context: Optional context for the graph
    
    Returns:
        List of results showing added observations per entity.
        Each result includes 'entity_created' flag indicating if entity was auto-created.
    
    Example:
        observations = [
            {
                "entityName": "Clinical Trial NCT12345",  # Will be created if doesn't exist
                "contents": ["Started in January 2024", "Expected completion December 2024"]
            }
        ]
        result = add_observations(observations)
        # result[0]["entity_created"] indicates if entity was auto-created
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_add_observations():
        return await knowledge_graph_manager.add_observations(observations, context)
    
    return asyncio.run(_async_add_observations())


def search_nodes(
    query: str, 
    context: Optional[str] = None,
    cache_dir: Optional[str] = None
, 
    top_k: Optional[int] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for nodes in the knowledge graph using BM25 indexing.
    
    Args:
        query: Search query string
        context: Optional context for the graph
        top_k: Maximum number of results to return
    
    Returns:
        Dictionary with 'entities' and 'relations' lists
    
    Example:
        result = search_nodes("diabetes treatment")
        # Returns: {"entities": [...], "relations": [...]}
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_search_nodes():
        graph_result = await knowledge_graph_manager.search_nodes(query, context, top_k)
        return graph_result.to_dict()
    
    return asyncio.run(_async_search_nodes())


def open_nodes(
    entity_names: List[str], 
    context: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve specific nodes by name along with their relations.
    
    Args:
        entity_names: List of entity names to retrieve
        context: Optional context for the graph
    
    Returns:
        Dictionary with 'entities' and 'relations' lists
    
    Example:
        result = open_nodes(["Dr. Jane Smith", "Clinical Trial NCT12345"])
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_open_nodes():
        graph_result = await knowledge_graph_manager.open_nodes(entity_names, context)
        return graph_result.to_dict()
    
    return asyncio.run(_async_open_nodes())

def list_databases(cache_dir: Optional[str] = None) -> Dict[str, Union[List[str], str]]:
    """
    List available knowledge graph databases in global location.
    
    Returns:
        Dictionary with databases list and storage location path
    
    Example:
        databases = list_databases()
        print(f"Storage location: {databases['location']}")
        print(f"Available databases: {databases['databases']}")
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_list_databases():
        return await knowledge_graph_manager.list_databases()
    
    return asyncio.run(_async_list_databases())


def visualize_graph(
    output_path: str,
    context: Optional[str] = None,
    cache_dir: Optional[str] = None,
    layout: str = "spring",
    figsize: tuple = (12, 8),
    node_size_scale: float = 1.0,
    edge_width_scale: float = 1.0,
    show_labels: bool = True,
    show_entity_types: bool = True,
    show_observations: bool = False,
    max_nodes: int = 100
) -> Optional[str]:
    """
    Visualize the knowledge graph using NetworkX and Matplotlib.
    
    Args:
        output_path: Path to save the figure
        context: Optional context for the graph
        layout: Layout algorithm ('spring', 'circular', 'random', 'shell', 'kamada_kawai')
        figsize: Figure size as (width, height)
        node_size_scale: Scale factor for node sizes
        edge_width_scale: Scale factor for edge widths
        show_labels: Whether to show node labels
        show_entity_types: Whether to color nodes by entity type
        show_observations: Whether to include observation count in labels
        max_nodes: Maximum number of nodes to display (for performance)
        
    Returns:
        Path to saved figure if output_path provided, None otherwise
        
    Example:
        # Save to file
        path = visualize_graph(output_path="my_graph.png", layout="spring")
        
        # Display interactively
        visualize_graph(show_entity_types=True, show_observations=True)
        
        # Large graph with performance settings
        visualize_graph(max_nodes=50, node_size_scale=0.8)
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_visualize_graph():
        return await knowledge_graph_manager.visualize_graph(
            context=context,
            output_path=output_path,
            layout=layout,
            figsize=figsize,
            node_size_scale=node_size_scale,
            edge_width_scale=edge_width_scale,
            show_labels=show_labels,
            show_entity_types=show_entity_types,
            show_observations=show_observations,
            max_nodes=max_nodes
        )
    
    return asyncio.run(_async_visualize_graph())

def clear_graph(
    context: str,
    cache_dir: Optional[str] = None
) -> None:
    """
    Clear a specified database of the knowledge graph.
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_clear_graph():
        return await knowledge_graph_manager.clear_graph(context)
    
    result = asyncio.run(_async_clear_graph())
    # Clear the cached manager after clearing the graph
    clear_manager_cache(cache_dir)
    return result


def get_graph_text_overview(
    context: Optional[str] = None,
    cache_dir: Optional[str] = None,
    max_entities: Optional[int] = None,
    max_observations_per_entity: int = 5,
    include_statistics: bool = True,
    group_by_type: bool = True,
) -> str:
    """
    Generate a text representation of the knowledge graph optimized for LLM reading.
    
    This provides a structured, readable text view of the entire graph including
    entities, their observations, and relationships - perfect for LLMs to understand
    the current state of the knowledge graph.
    
    Args:
        context: Optional context for the graph (e.g., 'research', 'clinical')
        max_entities: Maximum number of entities to include (None = all entities)
        max_observations_per_entity: Maximum observations to show per entity (default: 5)
        include_statistics: Whether to include graph statistics at the beginning (default: True)
        group_by_type: Whether to group entities by their type (default: True)
        cache_dir: Optional directory to cache the graph
    Returns:
        A formatted markdown string representing the entire graph structure
    
    Example:
        # Get full graph as text
        text = get_graph_text_overview()
        
        # Get graph with limits
        text = get_graph_text_overview(max_entities=20, max_observations_per_entity=3)
        
        # Get graph without statistics
        text = get_graph_text_overview(include_statistics=False, group_by_type=False)
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_get_text_representation():
        return await knowledge_graph_manager.get_text_representation(
            context=context,
            max_entities=max_entities,
            max_observations_per_entity=max_observations_per_entity,
            include_statistics=include_statistics,
            group_by_type=group_by_type
        )
    
    return asyncio.run(_async_get_text_representation())

def load_graph_data(
    context: str,
    cache_dir: Optional[str] = None
):
    """
    Load the memory graph from the database.
    """
    knowledge_graph_manager = _get_manager(cache_dir=cache_dir)
    async def _async_load_graph_data():
        return await knowledge_graph_manager.read_graph(context)
    
    results = asyncio.run(_async_load_graph_data())
    return results.to_dict()