"""
Tools that leverage the memory graph to manage the memory graph for the agent.

This module provides two simple tools:
1. AddToGraph - Add entities, relations, and observations to the memory graph
2. RetrieveFromGraph - Search and retrieve information from the memory graph
"""
from typing import Optional, List, Dict, Any, Annotated, Type
from langchain_core.tools import BaseTool, InjectedToolArg
from pydantic import BaseModel, Field
import json

from biodsa.memory.memory_graph import (
    create_entities, 
    create_relations, 
    add_observations, 
    search_nodes, 
    open_nodes, 
    get_graph_text_overview, 
    load_graph_data,
)

class Entity(BaseModel):
    name: str
    entity_type: str
    observations: List[str]

class Relation(BaseModel):
    from_entity: str
    to_entity: str
    relation_type: str

class AddToGraphInput(BaseModel):
    entities: Optional[List[Entity]] = Field(None, description="List of entities to create")
    relations: Optional[List[Relation]] = Field(None, description="List of relations to create between entities")
    observations: Optional[Entity] = Field(None, description="Entity with observations to add")

class AddToGraph(BaseTool):
    name: str = "add_to_graph"
    description: str = """Add information to the graph knowledge graph.
    
    Use this tool to store and organize research findings by:
    - Creating entities
    - Defining relationships between entities
    - Adding observations/notes to existing entities
    
    This helps build a structured knowledge base during the research process."""
    args_schema: Type[BaseModel] = AddToGraphInput
    database_name: str = "memory_graph"
    cache_dir: str = None

    def __init__(self, database_name: str = "memory_graph", cache_dir: str = None):
        super().__init__()
        self.database_name = database_name
        self.cache_dir = cache_dir

    def _run(
        self, 
        entities: Optional[List[Entity]] = None,
        relations: Optional[List[Relation]] = None,
        observations: Optional[Entity] = None,
    ) -> str:
        """
        Add entities, relations, or observations to the graph.
        
        Args:
            entities: list of Entity objects
                
            relations: list of Relation objects
                
            observations: list of observations to add to an existing entity (creates entities if they don't exist).
        
        Returns:
            JSON string with operation results
        """
        try:
            context = self.database_name
            results = {}
            
            # Process entities
            if entities:
                entities_dicts = []
                for e in entities:
                    if not isinstance(e, dict):
                        return json.dumps({
                            "success": False,
                            "error": f"Invalid entity format: expected dict, got {type(e).__name__}. Entity: {e}"
                        })
                    # Validate required keys
                    if "name" not in e or "entity_type" not in e:
                        return json.dumps({
                            "success": False,
                            "error": f"Entity missing required fields 'name' or 'entity_type': {e}"
                        })
                    entities_dicts.append(e)
                
                created = create_entities(entities_dicts, context=context, cache_dir=self.cache_dir)
                results["entities_created"] = {
                    "count": len(created),
                    "entities": created
                }
            
            # Process relations
            if relations:
                relations_dicts = []
                for r in relations:
                    if not isinstance(r, dict):
                        return json.dumps({
                            "success": False,
                            "error": f"Invalid relation format: expected dict, got {type(r).__name__}. Relation: {r}"
                        })
                    # Validate required keys
                    if "from_entity" not in r or "to_entity" not in r or "relation_type" not in r:
                        return json.dumps({
                            "success": False,
                            "error": f"Relation missing required fields 'from_entity', 'to_entity', or 'relation_type': {r}"
                        })
                    relations_dicts.append(r)
                
                created = create_relations(relations_dicts, context=context, cache_dir=self.cache_dir)
                results["relations_created"] = {
                    "count": len(created),
                    "relations": created
                }
            
            # Process observations
            if observations:
                if not isinstance(observations, dict):
                    return json.dumps({
                        "success": False,
                        "error": f"Invalid observations format: expected dict, got {type(observations).__name__}. Observations: {observations}"
                    })
                # Validate required keys
                if "name" not in observations or "observations" not in observations:
                    return json.dumps({
                        "success": False,
                        "error": f"Observations missing required fields 'name' or 'observations': {observations}"
                    })
                
                obs_dict = {
                    "entityName": observations["name"],
                    "contents": observations["observations"]
                }
                added = add_observations([obs_dict], context=context, cache_dir=self.cache_dir)
                results["observations_added"] = added
            
            if not results:
                return json.dumps({
                    "error": "No data provided. Please provide at least one of: entities, relations, or observations"
                })
            
            return json.dumps({
                "success": True,
                "results": results
            })
                
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON format: {str(e)}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error adding to graph: {str(e)}"
            })


class RetrieveFromGraphInput(BaseModel):
    query: Optional[str] = Field(None, description="Natural language search query to find relevant entities and relations")
    entity_names: Optional[str] = Field(None, description="JSON string list of exact entity names to retrieve with their relations")
    get_full_map: bool = Field(False, description="If True, returns a full text representation of the entire graph")
    top_k: int = Field(10, description="Maximum number of search results to return (only used with query)")
    max_entities: Optional[int] = Field(None, description="Maximum number of entities to include in full map (None = all, only used with get_full_map=True)")
    max_observations_per_entity: int = Field(5, description="Maximum observations to show per entity in full map (only used with get_full_map=True)")

class RetrieveFromGraph(BaseTool):
    name: str = "retrieve_from_graph"
    description: str = """Retrieve information from the graph knowledge graph.
    
    Use this tool to:
    - Get the full text representation of the entire graph (use get_full_map=True)
    - Search for entities and relations using natural language queries
    - Get specific entities by their exact names along with their connections
    
    This helps you find and review information stored in the graph."""
    args_schema: Type[BaseModel] = RetrieveFromGraphInput
    database_name: str = "memory_graph"
    cache_dir: str = None
    
    def __init__(self, database_name: str = "memory_graph", cache_dir: str = None):
        super().__init__()
        self.database_name = database_name
        self.cache_dir = cache_dir
    def _run(
        self, 
        query: Optional[str] = None,
        entity_names: Optional[str] = None,
        get_full_map: bool = False,
        top_k: int = 10,
        max_entities: Optional[int] = None,
        max_observations_per_entity: int = 5,
    ) -> str:
        """
        Search or retrieve information from the graph.
        
        Args:
            get_full_map: If True, returns a full text representation of the entire graph.
                This is useful to get an overview of all entities and relations in a readable format.
                Example: get_full_map=True
                
            query: Natural language search query to find relevant entities and relations.
                Example: "genes related to breast cancer", "datasets about mutations"
                
            entity_names: JSON string list of exact entity names to retrieve with their relations.
                Format: '["Entity1", "Entity2"]'
                Example: '["BRCA1", "Breast Cancer"]'
                
            top_k: Maximum number of search results to return (default: 10, only used with query)
            
            max_entities: Maximum number of entities to include in full graph (None = all, only used with get_full_map=True)
            
            max_observations_per_entity: Maximum observations to show per entity in full graph (default: 5, only used with get_full_map=True)
        
        Returns:
            JSON string with retrieved entities and relations, or text representation if get_full_graph=True
        """
        try:
            context = self.database_name
            
            # Get full map as text
            if get_full_map:
                text_repr = get_graph_text_overview(
                    context=context,
                    max_entities=max_entities,
                    max_observations_per_entity=max_observations_per_entity,
                    group_by_type=True,
                    include_statistics=True,
                    cache_dir=self.cache_dir
                )
                return text_repr
            
            # Search by query
            elif query:
                result = search_nodes(query, context=context, top_k=top_k, cache_dir=self.cache_dir)
                return json.dumps({
                    "success": True,
                    "search_query": query,
                    "results": result
                })
            
            # Retrieve specific entities
            elif entity_names:
                entity_names_list = json.loads(entity_names)
                result = open_nodes(entity_names_list, context=context, cache_dir=self.cache_dir)
                return json.dumps({
                    "success": True,
                    "requested_entities": entity_names_list,
                    "results": result
                })
            
            else:
                return json.dumps({
                    "error": "Please provide one of: 'get_full_map=True' for full map view, 'query' for searching, or 'entity_names' for retrieving specific entities"
                })
                
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON format: {str(e)}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error retrieving from graph: {str(e)}"
            })