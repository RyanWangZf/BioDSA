"""
Going to implement a local graph manager that can allow the agent to store and retrieve information from a graph,
as a way to be the internal knowledge graph memory for the agent.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple

# Optional visualization dependencies
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False

from .bm25_index import BM25SearchIndex, HAS_BM25, HAS_TIKTOKEN
from .schema import Entity, Relation, KnowledgeGraph, calculate_entities_hash

# File marker for safety
FILE_MARKER = {"type": "_biodsa", "source": "mcp-knowledge-graph"}
REPO_BASE_DIR = os.environ.get("REPO_BASE_DIR")

def get_default_memory_graph_cache_dir() -> Path:
    if REPO_BASE_DIR is None:
        return Path.home() / ".biodsa_memory" / "memory_graph"
    else:
        return Path(REPO_BASE_DIR) / ".biodsa_memory" / "memory_graph"

def get_memory_file_path(cache_dir: Path, context: Optional[str] = None) -> Path:
    """Get the file path for storing memory data."""
    filename = "memory.jsonl" if context is None else f"memory-{context}.jsonl"
    return cache_dir / filename

def get_index_file_path(cache_dir: Path, context: Optional[str] = None) -> Path:
    """Get the file path for storing BM25 index data."""
    filename = "index.pkl" if context is None else f"index-{context}.pkl"
    return cache_dir / filename


class KnowledgeGraphManager:
    """Manager class for interacting with the knowledge graph."""
    
    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = get_default_memory_graph_cache_dir()
        if isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._search_index = BM25SearchIndex()
        self._index_dirty = True  # Flag to track if index needs rebuilding
        
        # In-memory graph cache to avoid loading entire graph repeatedly
        self._cached_graph: Optional[KnowledgeGraph] = None
        self._cached_graph_context: Optional[str] = None
        self._cached_graph_file_mtime: Optional[float] = None
        
        # Cache for faster entity lookups
        self._entity_cache: Dict[str, Entity] = {}
        self._cache_dirty = True
        # Cache for faster relation lookups
        self._relation_cache: Dict[Tuple[str, str, str], Relation] = {}
        self._relation_cache_dirty = True

    async def _load_graph(self, context: Optional[str] = None) -> KnowledgeGraph:
        """Load the knowledge graph from file with intelligent caching."""
        file_path = get_memory_file_path(self._cache_dir, context)
        
        # Check if we can use cached graph
        if self._can_use_cached_graph(context, file_path):
            return self._cached_graph
        
        try:
            current_mtime = os.path.getmtime(file_path) if file_path.exists() else 0.0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            if not lines:
                graph = KnowledgeGraph(entities=[], relations=[])
                self._update_graph_cache(graph, context, current_mtime)
                return graph
            
            # Check first line for our file marker
            first_line = json.loads(lines[0])
            if first_line.get("type") != "_biodsa" or first_line.get("source") != "mcp-knowledge-graph":
                raise ValueError(
                    f"File {file_path} does not contain required _biodsa safety marker. "
                    f"This file may not belong to the knowledge graph system. "
                    f'Expected first line: {json.dumps(FILE_MARKER)}'
                )
            
            # Process remaining lines (skip metadata)
            entities = []
            relations = []
            
            for line in lines[1:]:
                try:
                    item = json.loads(line)
                    if item.get("type") == "entity":
                        # Remove the type field before creating Entity
                        entity_data = {k: v for k, v in item.items() if k != "type"}
                        entities.append(Entity.from_dict(entity_data))
                    elif item.get("type") == "relation":
                        # Remove the type field before creating Relation
                        relation_data = {k: v for k, v in item.items() if k != "type"}
                        relations.append(Relation.from_dict(relation_data))
                except json.JSONDecodeError:
                    # Skip corrupted lines
                    continue
            
            graph = KnowledgeGraph(entities=entities, relations=relations)
            
            # Update cache with loaded graph
            self._update_graph_cache(graph, context, current_mtime)
            
            # Mark entity/relation caches as dirty since graph was loaded
            self._cache_dirty = True
            self._relation_cache_dirty = True
            
            return graph
            
        except FileNotFoundError:
            # File doesn't exist - we'll create it with metadata on first save
            graph = KnowledgeGraph(entities=[], relations=[])
            self._update_graph_cache(graph, context, 0.0)
            return graph

    def _can_use_cached_graph(self, context: Optional[str], file_path: Path) -> bool:
        """Check if we can use the cached graph instead of loading from file."""
        if self._cached_graph is None:
            return False
        
        # Check if context matches
        if self._cached_graph_context != context:
            return False
        
        # Check if file has been modified since cache
        if not file_path.exists():
            # If file doesn't exist, we can use cache if we cached an empty graph for this location
            return self._cached_graph_file_mtime == 0.0
        
        try:
            current_mtime = os.path.getmtime(file_path)
            return current_mtime == self._cached_graph_file_mtime
        except OSError:
            return False

    def _update_graph_cache(self, graph: KnowledgeGraph, context: Optional[str], mtime: float) -> None:
        """Update the in-memory graph cache."""
        self._cached_graph = graph
        self._cached_graph_context = context
        self._cached_graph_file_mtime = mtime

    def _invalidate_graph_cache(self) -> None:
        """Invalidate the graph cache (call after saving changes)."""
        self._cached_graph = None
        self._cached_graph_context = None
        self._cached_graph_file_mtime = None

    async def _stream_entities_from_file(self, file_path: Path):
        """Generator that streams entities from file without loading entire graph."""
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = True
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Skip file marker (first line)
                        if first_line:
                            first_line = False
                            if data.get("type") == "_biodsa":
                                continue
                        
                        if data.get("type") == "entity":
                            entity_data = {k: v for k, v in data.items() if k != "type"}
                            yield Entity.from_dict(entity_data)
                            
                    except json.JSONDecodeError:
                        continue  # Skip invalid lines
        except FileNotFoundError:
            return

    async def _entity_exists_streaming(self, entity_name: str, context: Optional[str] = None) -> bool:
        """Check if entity exists by streaming through file (memory efficient)."""
        file_path = get_memory_file_path(self._cache_dir, context)
        
        async for entity in self._stream_entities_from_file(file_path):
            if entity.name == entity_name:
                return True
        return False

    async def _append_entities_to_file(self, entities: List[Entity], context: Optional[str] = None) -> None:
        """Append new entities to file without loading entire graph (memory efficient)."""
        file_path = get_memory_file_path(self._cache_dir, context)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # If file doesn't exist, create it with metadata
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(FILE_MARKER) + '\n')
        
        # Append entities to file
        with open(file_path, 'a', encoding='utf-8') as f:
            for entity in entities:
                entity_data = {"type": "entity", **entity.to_dict()}
                f.write(json.dumps(entity_data) + '\n')
        
        # Invalidate cache since file was modified
        self._invalidate_graph_cache()
        self._cache_dirty = True

    async def _save_graph(self, graph: KnowledgeGraph, context: Optional[str] = None) -> None:
        """Save the knowledge graph to file."""
        file_path = get_memory_file_path(self._cache_dir, context)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare lines to write
        lines = [json.dumps(FILE_MARKER)]
        
        # Add entities
        for entity in graph.entities:
            entity_data = {"type": "entity", **entity.to_dict()}
            lines.append(json.dumps(entity_data))
        
        # Add relations
        for relation in graph.relations:
            relation_data = {"type": "relation", **relation.to_dict()}
            lines.append(json.dumps(relation_data))
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        # Update the in-memory cache with the saved graph
        try:
            new_mtime = os.path.getmtime(file_path)
            self._update_graph_cache(graph, context, new_mtime)
        except OSError:
            # If we can't get the mtime, invalidate cache
            self._invalidate_graph_cache()
        
        # Mark caches as dirty since graph was modified
        self._cache_dirty = True
        self._relation_cache_dirty = True

    def _build_entity_cache(self, entities: List[Entity]) -> None:
        """Build entity cache for O(1) lookups."""
        self._entity_cache = {entity.name: entity for entity in entities}
        self._cache_dirty = False

    def _ensure_cache_built(self, entities: List[Entity]) -> None:
        """Ensure entity cache is built and up-to-date."""
        if self._cache_dirty or not self._entity_cache:
            self._build_entity_cache(entities)

    def _get_entity_fast(self, entity_name: str, entities: List[Entity]) -> Optional[Entity]:
        """Get entity with O(1) lookup using cache."""
        self._ensure_cache_built(entities)
        return self._entity_cache.get(entity_name)

    def _build_relation_cache(self, relations: List[Relation]) -> None:
        """Build relation cache for O(1) lookups."""
        self._relation_cache = {
            (r.from_entity, r.to_entity, r.relation_type): r 
            for r in relations
        }
        self._relation_cache_dirty = False

    def _ensure_relation_cache_built(self, relations: List[Relation]) -> None:
        """Ensure relation cache is built and up-to-date."""
        if self._relation_cache_dirty or not self._relation_cache:
            self._build_relation_cache(relations)

    def _relation_exists_fast(self, relation: Relation, relations: List[Relation]) -> bool:
        """Check if relation exists with O(1) lookup using cache."""
        self._ensure_relation_cache_built(relations)
        relation_key = (relation.from_entity, relation.to_entity, relation.relation_type)
        return relation_key in self._relation_cache

    async def create_entities(self, entities: List[Entity], context: Optional[str] = None) -> List[Entity]:
        """Create new entities in the knowledge graph."""
        # For small batches, use streaming to avoid loading entire graph
        if len(entities) <= 10:  # Threshold for streaming vs full load
            return await self._create_entities_streaming(entities, context)
        
        # For large batches, load full graph (amortized cost)
        graph = await self._load_graph(context)
        
        # Use cache for O(1) entity existence checks
        self._ensure_cache_built(graph.entities)
        new_entities = [e for e in entities if e.name not in self._entity_cache]
        
        if new_entities:
            # Add new entities to graph
            graph.entities.extend(new_entities)
            await self._save_graph(graph, context)
            
            # Update search index
            if self._search_index.is_built():
                # Incrementally update existing index
                self._search_index.add_entities_incremental(new_entities, graph.entities)
            else:
                # Build index from scratch (e.g., after clear_graph)
                self._search_index.build_index(graph.entities)
            
            # Save updated index to disk
            index_file_path = get_index_file_path(self._cache_dir, context)
            self._search_index.save_to_disk(index_file_path)
            # Index is now up-to-date
            self._index_dirty = False
        
        return new_entities

    async def _create_entities_streaming(self, entities: List[Entity], context: Optional[str] = None) -> List[Entity]:
        """Memory-efficient entity creation using streaming for existence checks."""
        new_entities = []
        
        # Check each entity for existence using streaming
        for entity in entities:
            if not await self._entity_exists_streaming(entity.name, context):
                new_entities.append(entity)
        
        if new_entities:
            # Append new entities to file without loading entire graph
            await self._append_entities_to_file(new_entities, context)
            
            # Update search index incrementally if available
            if self._search_index.is_built():
                # We need all entities for incremental update, so load graph
                graph = await self._load_graph(context)
                self._search_index.add_entities_incremental(new_entities, graph.entities)
                
                # Save updated index to disk
                index_file_path = get_index_file_path(self._cache_dir, context)
                self._search_index.save_to_disk(index_file_path)
                self._index_dirty = False
            else:
                # Mark index as needing rebuild
                self._index_dirty = True
        
        return new_entities

    async def create_relations(self, relations: List[Relation], context: Optional[str] = None) -> List[Relation]:
        """
        Create new relations in the knowledge graph.
        
        Automatically creates entities for any entity names referenced in relations
        that don't already exist in the graph.
        """
        graph = await self._load_graph(context)
        
        # Get all existing entity names
        existing_entity_names = {entity.name for entity in graph.entities}
        
        # Find all entity names referenced in the new relations
        referenced_entity_names = set()
        for relation in relations:
            referenced_entity_names.add(relation.from_entity)
            referenced_entity_names.add(relation.to_entity)
        
        # Find entities that are referenced but don't exist
        missing_entity_names = referenced_entity_names - existing_entity_names
        
        # Automatically create missing entities
        if missing_entity_names:
            new_entities = [
                Entity(
                    name=name,
                    entity_type="auto_created",
                    observations=[f"Auto-created from relation on {self._get_timestamp()}"]
                )
                for name in sorted(missing_entity_names)
            ]
            graph.entities.extend(new_entities)
            # Clear entity cache since we added new entities
            self._entity_cache.clear()
        
        # Use cache for O(1) relation existence checks
        self._ensure_relation_cache_built(graph.relations)
        new_relations = [r for r in relations if not self._relation_exists_fast(r, graph.relations)]
        
        if new_relations or missing_entity_names:
            # Add new relations to graph
            graph.relations.extend(new_relations)
            await self._save_graph(graph, context)
        
        return new_relations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def add_observations(self, observations: List[Dict[str, Union[str, List[str]]]], context: Optional[str] = None) -> List[Dict[str, Union[str, List[str]]]]:
        """Add observations to existing entities, or create new entities if they don't exist."""
        graph = await self._load_graph(context)
        results = []
        entities_updated = []
        entities_created = []
        
        for obs in observations:
            entity_name = obs["entityName"]
            contents = obs["contents"]
            
            # Find the entity using fast cache lookup
            entity = self._get_entity_fast(entity_name, graph.entities)
            
            if not entity:
                # Entity doesn't exist, create a new one
                from .schema import Entity
                entity = Entity(
                    name=entity_name,
                    entity_type="auto_generated",  # Default type for auto-created entities
                    observations=list(contents)  # Add all observations to new entity
                )
                graph.entities.append(entity)
                entities_created.append(entity)
                
                results.append({
                    "entityName": entity_name,
                    "addedObservations": list(contents),
                    "entity_created": True
                })
            else:
                # Entity exists, add new observations
                new_observations = [content for content in contents if content not in entity.observations]
                if new_observations:
                    entity.observations.extend(new_observations)
                    entities_updated.append(entity)
                
                results.append({
                    "entityName": entity_name,
                    "addedObservations": new_observations,
                    "entity_created": False
                })
        
        # Save if any entities were created or updated
        if entities_updated or entities_created:
            await self._save_graph(graph, context)
            
            # Update search index
            if self._search_index.is_built():
                # Add newly created entities to index
                if entities_created:
                    self._search_index.add_entities_incremental(entities_created, graph.entities)
                
                # Update modified entities in index
                for entity in entities_updated:
                    self._search_index.update_entity_incremental(entity.name, entity, graph.entities)
                
                # Save updated index to disk
                index_file_path = get_index_file_path(self._cache_dir, context)
                self._search_index.save_to_disk(index_file_path)
                # Index is now up-to-date
                self._index_dirty = False
            else:
                # Mark index as needing rebuild
                self._index_dirty = True
        
        return results

    async def delete_entities(self, entity_names: List[str], context: Optional[str] = None) -> None:
        """Delete entities and their associated relations."""
        graph = await self._load_graph(context)
        
        # Check which entities actually exist to delete using cache
        self._ensure_cache_built(graph.entities)
        entities_to_delete = [name for name in entity_names if name in self._entity_cache]
        
        if entities_to_delete:
            # Convert to set for O(1) lookups
            entity_names_set = set(entity_names)
            
            # Remove entities
            graph.entities = [e for e in graph.entities if e.name not in entity_names_set]
            
            # Remove relations involving deleted entities (O(1) lookups)
            graph.relations = [
                r for r in graph.relations 
                if r.from_entity not in entity_names_set and r.to_entity not in entity_names_set
            ]
            
            await self._save_graph(graph, context)
            
            # Incrementally update search index
            if self._search_index.is_built():
                self._search_index.remove_entities_incremental(entities_to_delete, graph.entities)
                # Save updated index to disk
                index_file_path = get_index_file_path(self._cache_dir, context)
                self._search_index.save_to_disk(index_file_path)
                # Index is now up-to-date
                self._index_dirty = False
            else:
                # Mark index as needing rebuild
                self._index_dirty = True

    async def delete_observations(self, deletions: List[Dict[str, Union[str, List[str]]]], context: Optional[str] = None) -> None:
        """Delete specific observations from entities."""
        graph = await self._load_graph(context)
        entities_updated = []
        
        for deletion in deletions:
            entity_name = deletion["entityName"]
            observations_to_delete = deletion["observations"]
            
            # Use fast cache lookup
            entity = self._get_entity_fast(entity_name, graph.entities)
            if entity:
                original_count = len(entity.observations)
                entity.observations = [
                    obs for obs in entity.observations 
                    if obs not in observations_to_delete
                ]
                # Track if entity was actually modified
                if len(entity.observations) != original_count:
                    entities_updated.append(entity)
        
        if entities_updated:
            await self._save_graph(graph, context)
            
            # Incrementally update search index for modified entities
            if self._search_index.is_built():
                for entity in entities_updated:
                    self._search_index.update_entity_incremental(entity.name, entity, graph.entities)
                
                # Save updated index to disk
                index_file_path = get_index_file_path(self._cache_dir, context)
                self._search_index.save_to_disk(index_file_path)
                # Index is now up-to-date
                self._index_dirty = False
            else:
                # Mark index as needing rebuild
                self._index_dirty = True

    async def delete_relations(self, relations: List[Relation], context: Optional[str] = None) -> None:
        """Delete specific relations from the graph."""
        graph = await self._load_graph(context)
        
        # Create set for O(1) lookup of relations to delete
        relations_to_delete_keys = {
            (r.from_entity, r.to_entity, r.relation_type) for r in relations
        }
        
        # Filter out relations to delete (still O(n) but with O(1) lookups)
        original_count = len(graph.relations)
        graph.relations = [
            r for r in graph.relations 
            if (r.from_entity, r.to_entity, r.relation_type) not in relations_to_delete_keys
        ]
        
        # Only save if relations were actually deleted
        if len(graph.relations) != original_count:
            await self._save_graph(graph, context)

    async def read_graph(self, context: Optional[str] = None) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self._load_graph(context)
    
    async def _ensure_index_built(self, context: Optional[str] = None) -> None:
        """Ensure the search index is built and up-to-date."""
        # Load current graph to check entities
        graph = await self._load_graph(context)
        
        # Check if current index is valid for these entities
        if not self._index_dirty and self._search_index.is_valid_for_entities(graph.entities):
            return
        
        # Try to load index from disk first
        index_file_path = get_index_file_path(self._cache_dir, context)
        entities_hash = calculate_entities_hash(graph.entities)
        
        if self._search_index.load_from_disk(index_file_path, entities_hash):
            # Successfully loaded from disk
            self._index_dirty = False
            return
        
        # Need to rebuild index from scratch
        self._search_index.build_index(graph.entities)
        
        # Save the newly built index to disk
        self._search_index.save_to_disk(index_file_path)
        
        self._index_dirty = False
    
    async def rebuild_search_index(self, context: Optional[str] = None) -> None:
        """Manually rebuild the search index."""
        graph = await self._load_graph(context)
        self._search_index.build_index(graph.entities)
        
        # Save the newly built index to disk
        index_file_path = get_index_file_path(self._cache_dir, context)
        self._search_index.save_to_disk(index_file_path)
        
        self._index_dirty = False

    async def search_nodes(self, query: str, context: Optional[str] = None, top_k: Optional[int] = None) -> KnowledgeGraph:
        """Search for nodes matching the query using BM25 indexing for fast retrieval."""
        # Ensure search index is up-to-date
        await self._ensure_index_built(context)
        
        # Get matching entity names using BM25 search
        matching_entity_names = self._search_index.search(query, top_k)
        
        if not matching_entity_names:
            return KnowledgeGraph(entities=[], relations=[])
        
        # Load graph and filter entities by matching names
        graph = await self._load_graph(context)
        matching_entity_names_set = set(matching_entity_names)
        
        # Filter entities by matching names (preserving BM25 order)
        filtered_entities = []
        entity_name_to_entity = {entity.name: entity for entity in graph.entities}
        
        for entity_name in matching_entity_names:
            if entity_name in entity_name_to_entity:
                filtered_entities.append(entity_name_to_entity[entity_name])
        
        # Filter relations to only include those between filtered entities
        filtered_relations = [
            r for r in graph.relations 
            if r.from_entity in matching_entity_names_set and r.to_entity in matching_entity_names_set
        ]
        
        return KnowledgeGraph(entities=filtered_entities, relations=filtered_relations)

    async def open_nodes(self, names: List[str], context: Optional[str] = None) -> KnowledgeGraph:
        """Open specific nodes by name."""
        graph = await self._load_graph(context)
        
        # Filter entities by names
        filtered_entities = [e for e in graph.entities if e.name in names]
        filtered_entity_names = {entity.name for entity in filtered_entities}
        
        # Filter relations to only include those between filtered entities
        filtered_relations = [
            r for r in graph.relations 
            if r.from_entity in filtered_entity_names and r.to_entity in filtered_entity_names
        ]
        
        return KnowledgeGraph(entities=filtered_entities, relations=filtered_relations)

    async def list_databases(self) -> Dict[str, Union[List[str], str]]:
        """List available databases in global storage location."""

        result = {
            "databases": [],
            "location": str(get_default_memory_graph_cache_dir())
        }

        cache_dir = self._cache_dir
        
        # Check global directory
        try:
            if cache_dir.exists():
                files = list(cache_dir.glob("*.jsonl"))
                databases = []
                for file in files:
                    if file.name == "memory.jsonl":
                        databases.append("default")
                    elif file.name.startswith("memory-") and file.name.endswith(".jsonl"):
                        databases.append(file.name[7:-6])  # Remove "memory-" prefix and ".jsonl" suffix
                result["databases"] = sorted(databases)
        except (OSError, PermissionError):
            # Directory doesn't exist or can't read
            result["databases"] = []
        
        return result
    
    async def get_search_stats(self, context: Optional[str] = None) -> Dict[str, Union[int, bool, str]]:
        """Get statistics about the search index."""
        await self._ensure_index_built(context)
        
        # Check if index file exists on disk
        index_file_path = get_index_file_path(self._cache_dir, context)
        index_file_exists = index_file_path.exists()
        index_file_size = index_file_path.stat().st_size if index_file_exists else 0
        
        return {
            "index_built": self._search_index.is_built(),
            "total_entities": len(self._search_index.entity_names),
            "bm25_available": HAS_BM25,
            "search_backend": "BM25" if HAS_BM25 else "Linear",
            "index_dirty": self._index_dirty,
            "index_persistent": True,  # Now we support persistence
            "index_file_exists": index_file_exists,
            "index_file_size_bytes": index_file_size,
            "entities_hash": self._search_index._entities_hash
        }
    
    async def clear_search_index(self, context: Optional[str] = None) -> None:
        """Clear the in-memory index and delete the index file."""
        # Clear in-memory index
        self._search_index.clear()
        self._index_dirty = True
        
        # Delete index file if it exists
        index_file_path = get_index_file_path(self._cache_dir, context)
        if index_file_path.exists():
            try:
                index_file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete index file: {e}")
    
    async def clear_graph(self, context: Optional[str] = None) -> None:
        """Clear the entire knowledge graph (entities, relations) and search index."""
        # Create an empty graph
        empty_graph = KnowledgeGraph(entities=[], relations=[])
        
        # Save empty graph to disk
        await self._save_graph(empty_graph, context)
        
        # Clear search index
        await self.clear_search_index(context)
        
        print(f"✅ Cleared entire knowledge graph and search index")
    
    async def delete_graph_file(self, context: Optional[str] = None) -> None:
        """Delete the graph file and index file completely from disk."""
        # Delete graph file
        graph_file_path = get_memory_file_path(self._cache_dir, context)
        if graph_file_path.exists():
            try:
                graph_file_path.unlink()
                print(f"✅ Deleted graph file: {graph_file_path}")
            except Exception as e:
                print(f"Warning: Failed to delete graph file: {e}")
        
        # Delete index file  
        index_file_path = get_index_file_path(self._cache_dir, context)
        if index_file_path.exists():
            try:
                index_file_path.unlink()
                print(f"✅ Deleted index file: {index_file_path}")
            except Exception as e:
                print(f"Warning: Failed to delete index file: {e}")
        
        # Clear in-memory state
        self._search_index.clear()
        self._index_dirty = True

    async def visualize_graph(self, 
                            output_path: str,
                            context: Optional[str] = None, 
                            location: Optional[str] = None,
                            layout: str = "spring",
                            figsize: tuple = (12, 8),
                            node_size_scale: float = 1.0,
                            edge_width_scale: float = 1.0,
                            show_labels: bool = True,
                            show_entity_types: bool = True,
                            show_observations: bool = False,
                            max_nodes: int = 100) -> Optional[str]:
        """
        Visualize the knowledge graph using NetworkX and Matplotlib.
        
        Args:
            context: Optional context for the graph
            location: Storage location ('project' or 'global')
            output_path: Path to save the figure (if None, displays interactively)
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
        """
        if not HAS_VISUALIZATION:
            raise ImportError(
                "Visualization dependencies not available. "
                "Install with: pip install networkx matplotlib"
            )
        
        # Load the graph
        graph = await self._load_graph(context)
        
        if not graph.entities and not graph.relations:
            print("⚠️ Empty graph - nothing to visualize")
            return None
        
        # Limit nodes for performance
        entities_to_show = graph.entities[:max_nodes]
        if len(graph.entities) > max_nodes:
            print(f"📊 Showing first {max_nodes} of {len(graph.entities)} entities for performance")
        
        # Create NetworkX graph
        G = nx.DiGraph()  # Directed graph for relations
        
        # Add nodes (entities)
        for entity in entities_to_show:
            node_label = entity.name
            if show_observations and entity.observations:
                node_label += f" ({len(entity.observations)} obs)"
            
            G.add_node(
                entity.name,
                label=node_label,
                entity_type=entity.entity_type,
                observation_count=len(entity.observations)
            )
        
        # Add edges (relations)
        entity_names = {e.name for e in entities_to_show}
        relation_counts = {}  # Track multiple relations between same entities
        
        for relation in graph.relations:
            if relation.from_entity in entity_names and relation.to_entity in entity_names:
                edge_key = (relation.from_entity, relation.to_entity)
                if edge_key in relation_counts:
                    relation_counts[edge_key] += 1
                else:
                    relation_counts[edge_key] = 1
                
                G.add_edge(
                    relation.from_entity,
                    relation.to_entity,
                    relation_type=relation.relation_type,
                    edge_count=relation_counts[edge_key]
                )
        
        return self._render_networkx_graph(G, layout, figsize, node_size_scale, 
                                         edge_width_scale, show_labels, show_entity_types, 
                                         show_observations, output_path)

    def _render_networkx_graph(self, G, layout, figsize, node_size_scale, 
                              edge_width_scale, show_labels, show_entity_types, 
                              show_observations, output_path):
        """Render the NetworkX graph with matplotlib."""
        # Create figure
        plt.figure(figsize=figsize)
        plt.title("Knowledge Graph Visualization", fontsize=16, fontweight='bold')
        
        # Choose layout algorithm
        layout_funcs = {
            'spring': nx.spring_layout,
            'circular': nx.circular_layout,
            'random': nx.random_layout,
            'shell': nx.shell_layout,
            'kamada_kawai': nx.kamada_kawai_layout
        }
        
        if layout not in layout_funcs:
            print(f"⚠️ Unknown layout '{layout}', using 'spring'")
            layout = 'spring'
        
        try:
            pos = layout_funcs[layout](G, k=1, iterations=50)
        except Exception:
            # Fallback to spring layout if chosen layout fails
            pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Prepare node colors and sizes
        if show_entity_types:
            # Get unique entity types and assign colors
            entity_types = list(set(G.nodes[node].get('entity_type', 'unknown') for node in G.nodes()))
            colors = plt.cm.Set3(range(len(entity_types)))
            type_to_color = dict(zip(entity_types, colors))
            node_colors = [type_to_color[G.nodes[node].get('entity_type', 'unknown')] for node in G.nodes()]
        else:
            node_colors = 'lightblue'
        
        # Node sizes based on observation count
        if show_observations:
            base_size = 300 * node_size_scale
            node_sizes = [
                base_size + (G.nodes[node].get('observation_count', 0) * 50 * node_size_scale)
                for node in G.nodes()
            ]
        else:
            node_sizes = 500 * node_size_scale
        
        # Edge widths based on relation count
        edge_widths = [
            G.edges[edge].get('edge_count', 1) * edge_width_scale
            for edge in G.edges()
        ]
        
        # Draw the graph
        nx.draw_networkx_nodes(G, pos, 
                              node_color=node_colors, 
                              node_size=node_sizes, 
                              alpha=0.8)
        
        nx.draw_networkx_edges(G, pos, 
                              width=edge_widths, 
                              alpha=0.6, 
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->')
        
        # Add labels
        if show_labels:
            labels = {node: G.nodes[node].get('label', node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
        
        # Add edge labels (relation types)
        if len(G.edges()) < 50:  # Only show edge labels for smaller graphs
            edge_labels = {edge: G.edges[edge].get('relation_type', '') for edge in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
        
        # Create legend
        legend_elements = []
        
        # Entity type legend
        if show_entity_types and len(entity_types) > 1:
            for entity_type, color in type_to_color.items():
                legend_elements.append(
                    mpatches.Patch(color=color, label=f"Type: {entity_type}")
                )
        
        # Graph statistics legend
        stats_text = (
            f"Nodes: {len(G.nodes())}\n"
            f"Edges: {len(G.edges())}\n"
            f"Layout: {layout}"
        )
        legend_elements.append(mpatches.Patch(color='white', label=stats_text))
        
        if legend_elements:
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save or show
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Graph visualization saved to: {output_path}")
        return str(output_path)

    async def get_graph_statistics(self, context: Optional[str] = None) -> Dict[str, Union[int, float, Dict]]:
        """Get detailed statistics about the knowledge graph structure."""
        graph = await self._load_graph(context)
        
        if not graph.entities:
            return {
                "total_entities": 0,
                "total_relations": 0,
                "entity_types": {},
                "relation_types": {},
                "avg_observations_per_entity": 0.0,
                "connectivity": {
                    "connected_entities": 0,
                    "isolated_entities": 0,
                    "avg_connections_per_entity": 0.0
                }
            }
        
        # Entity statistics
        entity_types = {}
        total_observations = 0
        
        for entity in graph.entities:
            entity_type = entity.entity_type
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            total_observations += len(entity.observations)
        
        # Relation statistics
        relation_types = {}
        entity_connections = {}
        
        for relation in graph.relations:
            rel_type = relation.relation_type
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
            
            # Track connections
            for entity_name in [relation.from_entity, relation.to_entity]:
                if entity_name not in entity_connections:
                    entity_connections[entity_name] = 0
                entity_connections[entity_name] += 1
        
        # Connectivity analysis
        connected_entities = len(entity_connections)
        isolated_entities = len(graph.entities) - connected_entities
        avg_connections = sum(entity_connections.values()) / len(entity_connections) if entity_connections else 0
        
        return {
            "total_entities": len(graph.entities),
            "total_relations": len(graph.relations),
            "entity_types": entity_types,
            "relation_types": relation_types,
            "avg_observations_per_entity": total_observations / len(graph.entities) if graph.entities else 0.0,
            "connectivity": {
                "connected_entities": connected_entities,
                "isolated_entities": isolated_entities,
                "avg_connections_per_entity": avg_connections
            }
        }
    
    async def get_text_representation(
        self,
        context: Optional[str] = None,
        max_entities: Optional[int] = None,
        max_observations_per_entity: int = 5,
        include_statistics: bool = True,
        group_by_type: bool = True
    ) -> str:
        """
        Generate a text representation of the knowledge graph optimized for LLM reading.
        
        Args:
            context: Optional context for the graph
            max_entities: Maximum number of entities to include (None = all)
            max_observations_per_entity: Maximum observations to show per entity
            include_statistics: Whether to include graph statistics at the beginning
            group_by_type: Whether to group entities by type
            
        Returns:
            A formatted text string representing the graph structure
        """
        graph = await self._load_graph(context)
        
        if not graph.entities and not graph.relations:
            return "# Knowledge Graph\n\nThe knowledge graph is currently empty."
        
        lines = ["# Knowledge Graph"]
        lines.append("")
        
        # Add statistics if requested
        if include_statistics:
            stats = await self.get_graph_statistics(context)
            lines.append("## Summary Statistics")
            lines.append(f"- Total Entities: {stats['total_entities']}")
            lines.append(f"- Total Relations: {stats['total_relations']}")
            lines.append(f"- Entity Types: {', '.join(stats['entity_types'].keys())}")
            lines.append(f"- Relation Types: {', '.join(stats['relation_types'].keys())}")
            lines.append("")
        
        # Get all entity names that appear in relations (implicit entities)
        entities_in_relations = set()
        for relation in graph.relations:
            entities_in_relations.add(relation.from_entity)
            entities_in_relations.add(relation.to_entity)
        
        # Find entities that exist in relations but not as entity objects
        explicit_entity_names = {e.name for e in graph.entities}
        implicit_entity_names = entities_in_relations - explicit_entity_names
        
        # Create Entity objects for implicit entities (entities that only exist in relations)
        implicit_entities = [
            Entity(name=name, entity_type="implicit", observations=["(Referenced in relations but no entity data)"])
            for name in sorted(implicit_entity_names)
        ]
        
        # Combine explicit and implicit entities
        all_entities = list(graph.entities) + implicit_entities
        
        # Calculate connectivity (number of relations) for each entity
        entity_connectivity = {}
        for entity in all_entities:
            count = sum(1 for r in graph.relations 
                       if r.from_entity == entity.name or r.to_entity == entity.name)
            entity_connectivity[entity.name] = count
        
        # Sort entities by connectivity (most connected first), then by name
        sorted_entities = sorted(
            all_entities, 
            key=lambda e: (-entity_connectivity.get(e.name, 0), e.name)
        )
        
        # Limit entities if requested (now prioritizing most connected)
        entities_to_show = sorted_entities[:max_entities] if max_entities else sorted_entities
        
        if max_entities and len(all_entities) > max_entities:
            lines.append(f"*Showing {max_entities} of {len(all_entities)} entities (prioritized by connectivity)*")
            if implicit_entities:
                lines.append(f"*Note: {len(implicit_entities)} implicit entities found in relations*")
            lines.append("")
        
        # Build entity index for quick lookup
        entity_dict = {e.name: e for e in entities_to_show}
        entity_names_set = set(entity_dict.keys())
        
        # Section 1: List all entities with their observations
        lines.append("## Entities")
        lines.append("")
        
        if group_by_type:
            # Group by type
            entities_by_type = {}
            for entity in entities_to_show:
                entity_type = entity.entity_type or "uncategorized"
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)
            
            # Display by type
            for entity_type, entities in sorted(entities_by_type.items()):
                lines.append(f"### {entity_type.upper()}")
                lines.append("")
                
                for entity in sorted(entities, key=lambda e: (-entity_connectivity.get(e.name, 0), e.name)):
                    lines.extend(self._format_entity_simple(entity, max_observations_per_entity))
                
                lines.append("")
        else:
            # Display all entities without grouping
            for entity in entities_to_show:
                lines.extend(self._format_entity_simple(entity, max_observations_per_entity))
        
        # Section 2: List all relations
        relations_in_view = [r for r in graph.relations 
                            if r.from_entity in entity_names_set and r.to_entity in entity_names_set]
        
        if relations_in_view:
            lines.append("## Relations")
            lines.append("")
            for relation in relations_in_view:
                lines.append(f"{relation.from_entity} - {relation.relation_type} -> {relation.to_entity}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_entity_simple(
        self, 
        entity: Entity,
        max_observations: int
    ) -> List[str]:
        """Format a single entity with its observations only (no relations)."""
        lines = []
        
        # Entity name and type
        entity_display = entity.name
        if entity.entity_type:
            entity_display += f" ({entity.entity_type})"
        lines.append(f"**{entity_display}**")
        
        # Observations
        if entity.observations:
            obs_to_show = entity.observations[:max_observations]
            for obs in obs_to_show:
                lines.append(f"  - {obs}")
            
            if len(entity.observations) > max_observations:
                lines.append(f"  - ... and {len(entity.observations) - max_observations} more observations")
        else:
            lines.append(f"  - (no observations)")
        
        lines.append("")
        return lines
    
    def _format_entity_text(
        self, 
        entity: Entity, 
        graph: KnowledgeGraph, 
        entity_names_set: set,
        max_observations: int
    ) -> List[str]:
        """Format a single entity as text with its relations and observations."""
        lines = []
        
        # Entity name and type
        lines.append(f"### {entity.name}")
        if entity.entity_type:
            lines.append(f"*Type: {entity.entity_type}*")
        
        # Observations
        if entity.observations:
            obs_to_show = entity.observations[:max_observations]
            lines.append("")
            lines.append("**Observations:**")
            for obs in obs_to_show:
                lines.append(f"- {obs}")
            
            if len(entity.observations) > max_observations:
                lines.append(f"- *... and {len(entity.observations) - max_observations} more observations*")
        
        # Outgoing relations (this entity -> others)
        outgoing = [r for r in graph.relations 
                   if r.from_entity == entity.name and r.to_entity in entity_names_set]
        if outgoing:
            lines.append("")
            lines.append("**Relations:**")
            for rel in outgoing:
                lines.append(f"- {rel.relation_type} → {rel.to_entity}")
        
        # Incoming relations (others -> this entity)
        incoming = [r for r in graph.relations 
                   if r.to_entity == entity.name and r.from_entity in entity_names_set]
        if incoming:
            if not outgoing:  # Add header if not already added
                lines.append("")
                lines.append("**Relations:**")
            for rel in incoming:
                lines.append(f"- {rel.from_entity} → {rel.relation_type} → (this)")
        
        lines.append("")
        return lines

