"""
Risk Calculator Retrieval Module.

This module provides retrieval of clinical calculators based on
patient descriptions or clinical queries.

Retrieval modes:
1. BM25 (default): Fast keyword-based retrieval, no external dependencies
2. Embedding-based: Semantic search using sentence-transformers and FAISS
   (requires: pip install sentence-transformers faiss-cpu)
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np


@dataclass
class RetrievalResult:
    """Result from calculator retrieval."""
    calculator_id: str
    title: str
    purpose: str
    score: float
    metadata: Dict[str, Any]


class BM25Retriever:
    """
    BM25 retriever for text matching.
    No external dependencies required.
    """
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.
        
        Args:
            documents: List of documents to index
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Tokenize documents
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        
        # Calculate document lengths and average
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Build inverted index and document frequencies
        self.doc_freqs = {}  # term -> number of documents containing term
        self.inverted_index = {}  # term -> {doc_id: term_freq}
        
        for doc_id, tokens in enumerate(self.doc_tokens):
            term_freqs = {}
            for token in tokens:
                term_freqs[token] = term_freqs.get(token, 0) + 1
            
            for term, freq in term_freqs.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                    self.doc_freqs[term] = 0
                self.inverted_index[term][doc_id] = freq
                self.doc_freqs[term] += 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return tokens
    
    def _idf(self, term: str) -> float:
        """Calculate inverse document frequency for a term."""
        doc_freq = self.doc_freqs.get(term, 0)
        if doc_freq == 0:
            return 0
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_id: int) -> float:
        """Calculate BM25 score for a query against a document."""
        query_tokens = self._tokenize(query)
        doc_length = self.doc_lengths[doc_id]
        
        score = 0.0
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            if doc_id not in self.inverted_index[term]:
                continue
            
            tf = self.inverted_index[term][doc_id]
            idf = self._idf(term)
            
            # BM25 scoring formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            score += idf * numerator / denominator
        
        return score
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Retrieve top-k documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, score) tuples sorted by score descending
        """
        scores = []
        for doc_id in range(self.doc_count):
            score = self.score(query, doc_id)
            if score > 0:
                scores.append((doc_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class RiskCalcRetriever:
    """
    Retriever for clinical calculators.
    
    This class provides two modes of operation:
    1. BM25 retrieval (default): Fast, no external dependencies
    2. Embedding-based semantic search (requires sentence-transformers and faiss)
    
    Example:
        ```python
        # Default: BM25 retrieval (no extra dependencies)
        retriever = RiskCalcRetriever()
        
        # With embeddings (requires sentence-transformers, faiss-cpu)
        retriever = RiskCalcRetriever(use_embeddings=True)
        
        # Retrieve calculators for a patient description
        results = retriever.retrieve(
            query="65 year old with atrial fibrillation, considering anticoagulation",
            top_k=5
        )
        
        for result in results:
            print(f"{result.title}: {result.score:.3f}")
        ```
    """
    
    def __init__(
        self,
        calculators: Optional[Dict[str, Any]] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        use_embeddings: bool = False,
        use_full_riskcalcs: bool = True
    ):
        """
        Initialize the retriever.
        
        Args:
            calculators: Dict of calculator_id -> calculator_info. If None, loads from library.
            embedding_model: Name of the sentence-transformers model to use.
            use_embeddings: Whether to use embedding-based retrieval (default: False).
                          If True, requires: pip install sentence-transformers faiss-cpu
            use_full_riskcalcs: If True and calculators is None, load the full RiskCalcs dataset
                (2,164 calculators) from the original AgentMD repository.
        """
        # Load calculators
        if calculators is None:
            if use_full_riskcalcs:
                # Load the full RiskCalcs dataset (with lazy fetch and cache)
                from biodsa.tools.risk_calculators.calculator_library import get_riskcalcs
                try:
                    self.calculators = get_riskcalcs()
                    # Convert to retrieval format (title, purpose, etc.)
                    self.calculators = {
                        calc_id: {
                            "name": calc_data.get("title", "").strip(),
                            "purpose": calc_data.get("purpose", "").strip(),
                            "category": calc_data.get("specialty", "general").split(",")[0].strip().lower(),
                            "computation": calc_data.get("computation", ""),
                            "interpretation": calc_data.get("interpretation", ""),
                            "example": calc_data.get("example", ""),
                            "eligibility": calc_data.get("eligibility", ""),
                            **calc_data  # Include all original fields
                        }
                        for calc_id, calc_data in self.calculators.items()
                    }
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Failed to load full RiskCalcs dataset: {e}. "
                        "Falling back to common calculators."
                    )
                    from biodsa.tools.risk_calculators.calculator_library import COMMON_CALCULATORS
                    self.calculators = {k: v.to_dict() for k, v in COMMON_CALCULATORS.items()}
            else:
                from biodsa.tools.risk_calculators.calculator_library import COMMON_CALCULATORS
                self.calculators = {k: v.to_dict() for k, v in COMMON_CALCULATORS.items()}
        else:
            self.calculators = calculators
        
        self.calculator_ids = list(self.calculators.keys())
        
        # Build document texts for retrieval
        self._doc_texts = []
        for calc_id in self.calculator_ids:
            calc = self.calculators[calc_id]
            text = f"{calc.get('name', '')} {calc.get('purpose', '')} {calc.get('category', '')}"
            self._doc_texts.append(text)
        
        # Initialize retrieval method
        self.use_embeddings = use_embeddings
        self.model = None
        self.index = None
        self._bm25 = None
        
        if self.use_embeddings:
            self._initialize_embeddings(embedding_model)
        else:
            self._initialize_bm25()
    
    def _initialize_bm25(self):
        """Initialize BM25 retriever."""
        self._bm25 = BM25Retriever(self._doc_texts)
    
    def _initialize_embeddings(self, model_name: str):
        """Initialize the embedding model and index (lazy import)."""
        # Lazy import of heavy dependencies
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
        except ImportError as e:
            import warnings
            warnings.warn(
                f"Embedding dependencies not available: {e}. "
                "Install with: pip install sentence-transformers faiss-cpu\n"
                "Falling back to BM25 retrieval."
            )
            self.use_embeddings = False
            self._initialize_bm25()
            return
        
        try:
            self.model = SentenceTransformer(model_name)
            
            # Create embeddings for all calculators
            self.embeddings = self.model.encode(self._doc_texts, normalize_embeddings=True)
            
            # Create FAISS index
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            self.index.add(self.embeddings.astype(np.float32))
            
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to initialize embeddings: {e}. Falling back to BM25.")
            self.use_embeddings = False
            self._initialize_bm25()
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        category_filter: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant calculators for a query.
        
        Args:
            query: Patient description or clinical question
            top_k: Number of results to return
            category_filter: Optional category to filter results
            
        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        if self.use_embeddings:
            return self._retrieve_with_embeddings(query, top_k, category_filter)
        else:
            return self._retrieve_with_bm25(query, top_k, category_filter)
    
    def _retrieve_with_embeddings(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str]
    ) -> List[RetrievalResult]:
        """Retrieve using embedding similarity."""
        # Encode query
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        
        # Search index
        scores, indices = self.index.search(
            query_embedding.astype(np.float32), 
            min(top_k * 2, len(self.calculator_ids))
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
                
            calc_id = self.calculator_ids[idx]
            calc = self.calculators[calc_id]
            
            # Apply category filter
            if category_filter and calc.get("category", "").lower() != category_filter.lower():
                continue
            
            results.append(RetrievalResult(
                calculator_id=calc_id,
                title=calc.get("name", calc_id),
                purpose=calc.get("purpose", ""),
                score=float(score),
                metadata=calc
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _retrieve_with_bm25(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str]
    ) -> List[RetrievalResult]:
        """Retrieve using BM25."""
        # Get BM25 results
        bm25_results = self._bm25.retrieve(query, top_k=top_k * 2)
        
        results = []
        for doc_id, score in bm25_results:
            calc_id = self.calculator_ids[doc_id]
            calc = self.calculators[calc_id]
            
            # Apply category filter
            if category_filter and calc.get("category", "").lower() != category_filter.lower():
                continue
            
            results.append(RetrievalResult(
                calculator_id=calc_id,
                title=calc.get("name", calc_id),
                purpose=calc.get("purpose", ""),
                score=score,
                metadata=calc
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_calculator(self, calculator_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific calculator by ID."""
        return self.calculators.get(calculator_id)
    
    def list_all(self) -> List[str]:
        """List all available calculator IDs."""
        return list(self.calculator_ids)


def encode_query(
    query: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> np.ndarray:
    """
    Encode a query into an embedding vector.
    
    This is a standalone function for when you need just the embedding
    without the full retriever setup.
    
    Note: This function requires sentence-transformers.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers is required for encoding. "
            "Install with: pip install sentence-transformers"
        )
    
    model = SentenceTransformer(model_name)
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0]


def retrieve_calculators(
    query: str,
    top_k: int = 10,
    calculators: Optional[Dict[str, Any]] = None,
    use_embeddings: bool = False
) -> List[RetrievalResult]:
    """
    Convenience function to retrieve calculators without instantiating a retriever.
    
    Args:
        query: Patient description or clinical question
        top_k: Number of results to return
        calculators: Optional custom calculator dictionary
        use_embeddings: Whether to use embedding-based retrieval (default: False)
        
    Returns:
        List of RetrievalResult objects
    """
    retriever = RiskCalcRetriever(calculators=calculators, use_embeddings=use_embeddings)
    return retriever.retrieve(query, top_k=top_k)
