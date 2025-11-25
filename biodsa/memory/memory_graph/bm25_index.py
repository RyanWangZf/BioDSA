from typing import List, Optional, Dict
import pickle
import re
from pathlib import Path
from .schema import Entity
from .schema import calculate_entities_hash

# Try to import BM25 and tiktoken, gracefully handle failures
# DO NOT auto-install at module load time - this can cause blocking/hanging
try:
    import tiktoken
    tiktoken_encoder = tiktoken.encoding_for_model("gpt-4o")
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
    HAS_TIKTOKEN = True
except (ImportError, Exception) as e:
    # Import failed, fall back to linear search
    # User should manually install: pip install rank_bm25 tiktoken
    HAS_BM25 = False
    HAS_TIKTOKEN = False
    BM25Okapi = None
    tiktoken_encoder = None
    # Optional: log the failure for debugging
    print(f"Warning: BM25/tiktoken not available, falling back to linear search.")
    print(f"To enable fast search, install: pip install rank_bm25 tiktoken")
    print(f"Error details: {e}")

STOPWORD_SET = set(["a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"])


def _remove_stop_words(text: str) -> str:
    """Remove stop words from the text."""
    words = text.split()
    words = [word for word in words if word not in STOPWORD_SET]
    return " ".join(words)


def tokenize_text(text: str) -> List[str]:
    """Simple tokenization for BM25 indexing."""
    # Convert to lowercase and remove stop words
    text = _remove_stop_words(text.lower())
    
    # use tiktokens to remove some wrong words
    tokens = tiktoken_encoder.encode(text)
    text = tiktoken_encoder.decode(tokens)
    # Always use regex-based tokenization for now (tiktoken might cause issues)
    tokens = re.findall(r'\b\w+\b', text)

    return tokens


class BM25SearchIndex:
    """BM25-based search index for fast entity search with persistent storage."""
    
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.entity_docs: List[str] = []
        self.entity_names: List[str] = []
        self.tokenized_docs: List[List[str]] = []
        self._is_built = False
        self._entities_hash: Optional[str] = None  # Hash of entities used to build index
        # Index mapping for O(1) entity position lookups
        self._name_to_index: Dict[str, int] = {}
    
    def build_index(self, entities: List[Entity]) -> None:
        """Build the BM25 index from entities."""
        if not HAS_BM25:
            # Fallback: just store entities for linear search
            self.entity_names = [entity.name for entity in entities]
            self.entity_docs = []
            for entity in entities:
                doc_parts = [
                    entity.name,
                    entity.entity_type,
                    *entity.observations
                ]
                self.entity_docs.append(" ".join(doc_parts))
            self._is_built = True
            return
        
        self.entity_names = []
        self.entity_docs = []
        self.tokenized_docs = []
        self._name_to_index = {}
        
        for i, entity in enumerate(entities):
            # Create a searchable document from entity data
            doc_parts = [
                entity.name,
                entity.entity_type,
                *entity.observations
            ]
            doc_text = " ".join(doc_parts)
            
            # Tokenize the document
            tokens = tokenize_text(doc_text)
            
            self.entity_names.append(entity.name)
            self.entity_docs.append(doc_text)
            self.tokenized_docs.append(tokens)
            self._name_to_index[entity.name] = i
        
        # Build BM25 index
        if self.tokenized_docs:
            # Optimized parameters for small document collections
            # k1=0.5 (lower term frequency saturation for small collections)
            # b=0.3 (less length normalization penalty)  
            # epsilon=0.5 (higher epsilon to boost small collection scores)
            self.bm25 = BM25Okapi(self.tokenized_docs, k1=0.5, b=0.3, epsilon=0.5)
        
        # Store hash of entities used to build this index
        self._entities_hash = calculate_entities_hash(entities)
        self._is_built = True
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """Search for entities using BM25 scoring."""
        if not self._is_built:
            return []
        
        if not HAS_BM25:
            # Fallback to simple string matching
            query_lower = query.lower()
            return [
                name for i, name in enumerate(self.entity_names)
                if query_lower in self.entity_docs[i].lower()
            ]
        
        if not self.bm25 or not self.tokenized_docs:
            return []
        
        # Tokenize query
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # For small collections (< 10 docs), BM25 often returns zeros
        # Use hybrid scoring: BM25 + simple token overlap
        if len(self.entity_names) < 10:
            # Pre-convert query to set for O(1) lookups
            query_set = set(query_tokens)
            query_len = len(query_tokens)
            
            # Vectorized overlap calculation using list comprehension + set operations
            overlap_scores = [
                len(query_set & set(doc_tokens)) / query_len if query_len > 0 else 0
                for doc_tokens in self.tokenized_docs
            ]
            
            # Vectorized score combination using list comprehension
            scores = [
                bm25_score if bm25_score > 0 else (overlap_score * 0.1 if overlap_score > 0 else 0.0)
                for bm25_score, overlap_score in zip(scores, overlap_scores)
            ]
        
        # Create scored results
        scored_entities = [
            (score, name) for score, name in zip(scores, self.entity_names)
            if score > 0  # Only return entities with positive scores
        ]
        
        # Sort by score (descending)
        scored_entities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top-k entity names
        if top_k:
            scored_entities = scored_entities[:top_k]
        
        return [name for _, name in scored_entities]
    
    def is_built(self) -> bool:
        """Check if the index is built."""
        return self._is_built
    
    def clear(self) -> None:
        """Clear the index."""
        self.bm25 = None
        self.entity_docs = []
        self.entity_names = []
        self.tokenized_docs = []
        self._is_built = False
        self._entities_hash = None
        self._name_to_index = {}
    
    def save_to_disk(self, file_path: Path) -> None:
        """
        Save the index to disk.
        
        Performance optimization: Skip saving for small/frequent updates.
        Index will be rebuilt from graph on next load if needed.
        """
        if not self._is_built:
            return
        
        # OPTIMIZATION: Skip frequent index saves to avoid blocking
        # Index will be lazily rebuilt from the graph file on next load
        # This dramatically improves performance during heavy add_to_graph operations
        
        # Only save if we have a large index (>50 entities) to avoid rebuilding cost
        if len(self.entity_names) < 50:
            # Small index - rebuilding is fast, skip save to avoid blocking
            return
        
        # Prepare data to save
        index_data = {
            'entity_names': self.entity_names,
            'entity_docs': self.entity_docs,
            'tokenized_docs': self.tokenized_docs,
            'entities_hash': self._entities_hash,
            'has_bm25': HAS_BM25,
            'bm25_data': None
        }
        
        # Save BM25 object if available  
        if HAS_BM25 and self.bm25 is not None:
            # BM25Okapi objects can be pickled
            index_data['bm25_data'] = self.bm25
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to pickle file (synchronous, but only for large indices now)
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(index_data, f)
        except Exception as e:
            print(f"Warning: Failed to save BM25 index: {e}")
    
    def load_from_disk(self, file_path: Path, entities_hash: str) -> bool:
        """Load the index from disk if it's valid for current entities."""
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'rb') as f:
                index_data = pickle.load(f)
            
            # Check if the index is for the current entities
            if index_data.get('entities_hash') != entities_hash:
                return False
            
            # Check if BM25 availability matches
            if index_data.get('has_bm25') != HAS_BM25:
                return False
            
            # Restore index data
            self.entity_names = index_data.get('entity_names', [])
            self.entity_docs = index_data.get('entity_docs', [])
            self.tokenized_docs = index_data.get('tokenized_docs', [])
            self._entities_hash = index_data.get('entities_hash')
            
            # Restore BM25 object if available
            if HAS_BM25 and index_data.get('bm25_data') is not None:
                self.bm25 = index_data['bm25_data']
            else:
                self.bm25 = None
            
            self._is_built = True
            return True
            
        except Exception as e:
            print(f"Warning: Failed to load BM25 index: {e}")
            return False
    
    def is_valid_for_entities(self, entities: List[Entity]) -> bool:
        """Check if the current index is valid for the given entities."""
        if not self._is_built:
            return False
        
        current_hash = calculate_entities_hash(entities)
        return self._entities_hash == current_hash
    
    def add_entities_incremental(self, new_entities: List[Entity], all_entities: List[Entity]) -> None:
        """Add new entities to the existing index incrementally."""
        if not self._is_built:
            # If index not built, build from scratch
            self.build_index(all_entities)
            return
        
        # Process new entities
        for entity in new_entities:
            # Create a searchable document from entity data
            doc_parts = [
                entity.name,
                entity.entity_type,
                *entity.observations
            ]
            doc_text = " ".join(doc_parts)
            
            # Add to our data structures
            new_index = len(self.entity_names)
            self.entity_names.append(entity.name)
            self.entity_docs.append(doc_text)
            self._name_to_index[entity.name] = new_index
            
            if HAS_BM25:
                # Tokenize the document
                tokens = tokenize_text(doc_text)
                self.tokenized_docs.append(tokens)
        
        # Rebuild BM25 index with all documents (unfortunately BM25Okapi doesn't support incremental addition)
        # Skip rebuild if we have too many documents to avoid blocking (rebuild will happen on next search if needed)
        if HAS_BM25 and self.tokenized_docs:
            if len(self.tokenized_docs) < 100:
                # For small graphs, rebuild immediately
                self.bm25 = BM25Okapi(self.tokenized_docs)
            else:
                # For large graphs, mark as dirty and rebuild lazily on next search
                self.bm25 = None
                self._is_built = False
        
        # Update hash for all entities
        self._entities_hash = calculate_entities_hash(all_entities)
    
    def remove_entities_incremental(self, entity_names_to_remove: List[str], all_entities: List[Entity]) -> None:
        """Remove entities from the existing index incrementally."""
        if not self._is_built:
            # If index not built, build from scratch
            self.build_index(all_entities)
            return
        
        # Find indices of entities to remove using O(1) lookups
        indices_to_remove = []
        entity_names_set = set(entity_names_to_remove)
        for entity_name in entity_names_set:
            index = self._name_to_index.get(entity_name)
            if index is not None:
                indices_to_remove.append(index)
        
        # Remove in reverse order to maintain correct indices
        for index in sorted(indices_to_remove, reverse=True):
            self.entity_names.pop(index)
            self.entity_docs.pop(index)
            if HAS_BM25 and index < len(self.tokenized_docs):
                self.tokenized_docs.pop(index)
        
        # Rebuild name-to-index mapping after removals
        self._name_to_index = {name: i for i, name in enumerate(self.entity_names)}
        
        # Rebuild BM25 index with remaining documents
        # Skip rebuild if we have too many documents to avoid blocking
        if HAS_BM25 and self.tokenized_docs:
            if len(self.tokenized_docs) < 100:
                # For small graphs, rebuild immediately
                self.bm25 = BM25Okapi(self.tokenized_docs)
            else:
                # For large graphs, mark as dirty and rebuild lazily on next search
                self.bm25 = None
                self._is_built = False
        elif HAS_BM25:
            self.bm25 = None
        
        # Update hash for all entities
        self._entities_hash = calculate_entities_hash(all_entities)
    
    def update_entity_incremental(self, entity_name: str, updated_entity: Entity, all_entities: List[Entity]) -> bool:
        """Update an existing entity in the index incrementally."""
        if not self._is_built:
            # If index not built, build from scratch
            self.build_index(all_entities)
            return True
        
        # Find the entity index using O(1) lookup
        entity_index = self._name_to_index.get(entity_name)
        if entity_index is None:
            # Entity not found, might be a new entity
            return False
        
        # Create updated document
        doc_parts = [
            updated_entity.name,
            updated_entity.entity_type,
            *updated_entity.observations
        ]
        doc_text = " ".join(doc_parts)
        
        # Update the entity data
        self.entity_names[entity_index] = updated_entity.name
        self.entity_docs[entity_index] = doc_text
        
        if HAS_BM25:
            # Update tokenized document
            tokens = tokenize_text(doc_text)
            self.tokenized_docs[entity_index] = tokens
            
            # Rebuild BM25 index (unfortunately no incremental update support)
            # Skip rebuild if we have too many documents to avoid blocking
            if self.tokenized_docs:
                if len(self.tokenized_docs) < 100:
                    # For small graphs, rebuild immediately
                    self.bm25 = BM25Okapi(self.tokenized_docs)
                else:
                    # For large graphs, mark as dirty and rebuild lazily on next search
                    self.bm25 = None
                    self._is_built = False
        
        # Update hash for all entities
        self._entities_hash = calculate_entities_hash(all_entities)
        return True

