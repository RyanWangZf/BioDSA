from dataclasses import dataclass
from typing import List, Dict
import json
import hashlib


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""
    name: str
    entity_type: str
    observations: List[str]

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "entityType": self.entity_type,
            "observations": self.observations
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Entity':
        return cls(
            name=data["name"],
            entity_type=data.get("entityType", ""),
            observations=data.get("observations", [])
        )


@dataclass
class Relation:
    """Represents a relation between entities in the knowledge graph."""
    from_entity: str
    to_entity: str
    relation_type: str

    def to_dict(self) -> Dict:
        return {
            "from": self.from_entity,
            "to": self.to_entity,
            "relationType": self.relation_type
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Relation':
        return cls(
            from_entity=data["from"],
            to_entity=data["to"],
            relation_type=data["relationType"]
        )


@dataclass
class KnowledgeGraph:
    """Represents the complete knowledge graph."""
    entities: List[Entity]
    relations: List[Relation]

    def to_dict(self) -> Dict:
        return {
            "entities": [entity.to_dict() for entity in self.entities],
            "relations": [relation.to_dict() for relation in self.relations]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeGraph':
        entities = [Entity.from_dict(e) for e in data.get("entities", [])]
        relations = [Relation.from_dict(r) for r in data.get("relations", [])]
        return cls(entities=entities, relations=relations)



def calculate_entities_hash(entities: List[Entity]) -> str:
    """
    Calculate a hash of entities to detect changes.
    Optimized to avoid expensive sorting and JSON serialization.
    """
    if not entities:
        return hashlib.md5(b"").hexdigest()
    
    # Fast hash: just count entities and use first/last few names
    # This is a lightweight check - doesn't need to be cryptographically perfect
    hash_input = f"{len(entities)}"
    
    # Use a subset of entity names for speed (first 10, last 10)
    if len(entities) <= 20:
        names = [e.name for e in entities]
    else:
        names = [e.name for e in entities[:10]] + [e.name for e in entities[-10:]]
    
    hash_input += "|".join(sorted(names))
    
    return hashlib.md5(hash_input.encode()).hexdigest()