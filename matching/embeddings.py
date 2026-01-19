"""
Embedding-based matching using sentence transformers.
"""

import logging
from typing import List, Optional, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from ingestion.models import Transaction
from ingestion.normalizers import DescriptionNormalizer

logger = logging.getLogger(__name__)


class EmbeddingMatcher:
    """Semantic matching using embeddings."""
    
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Initialize embedding matcher.
        
        Args:
            model_name: Name of sentence transformer model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_cache: Dict[str, np.ndarray] = {}
    
    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Get embedding for text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings
        
        Returns:
            Embedding vector
        """
        if not text:
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        # Clean text for matching
        cleaned = DescriptionNormalizer.clean_for_matching(text)
        
        # Check cache
        if use_cache and cleaned in self.embedding_cache:
            return self.embedding_cache[cleaned]
        
        # Generate embedding
        embedding = self.model.encode(cleaned, convert_to_numpy=True)
        
        # Cache it
        if use_cache:
            self.embedding_cache[cleaned] = embedding
        
        return embedding
    
    def calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # Normalize to 0-1 range (cosine similarity is already -1 to 1)
        # Convert numpy float32 to Python float for JSON serialization
        return float((similarity + 1.0) / 2.0)
    
    def build_index(self, transactions: List[Transaction]) -> faiss.Index:
        """
        Build FAISS index for fast similarity search.
        
        Args:
            transactions: List of transactions to index
        
        Returns:
            FAISS index
        """
        if not transactions:
            raise ValueError("Cannot build index from empty transaction list")
        
        # Get embeddings
        embeddings = []
        for tx in transactions:
            emb = self.get_embedding(tx.description)
            embeddings.append(emb)
        
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product (for cosine similarity)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        index.add(embeddings)
        
        logger.info(f"Built FAISS index with {len(transactions)} transactions")
        
        return index
    
    def find_similar(
        self,
        query_text: str,
        transactions: List[Transaction],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[Transaction, float]]:
        """
        Find similar transactions using FAISS.
        
        Args:
            query_text: Text to search for
            transactions: List of candidate transactions
            top_k: Number of results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of (transaction, similarity_score) tuples
        """
        if not transactions:
            return []
        
        # Build index
        index = self.build_index(transactions)
        
        # Get query embedding
        query_emb = self.get_embedding(query_text)
        query_emb = query_emb.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_emb)
        
        # Search
        similarities, indices = index.search(query_emb, min(top_k, len(transactions)))
        
        # Filter by threshold and return
        results = []
        for i, (sim, idx) in enumerate(zip(similarities[0], indices[0])):
            if sim >= threshold and idx < len(transactions):
                results.append((transactions[idx], float(sim)))
        
        return results
    
    def match_transactions(
        self,
        bank_tx: Transaction,
        ledger_transactions: List[Transaction],
        threshold: float = 0.5
    ) -> Optional[Tuple[Transaction, float]]:
        """
        Find best matching ledger transaction for a bank transaction.
        
        Args:
            bank_tx: Bank transaction to match
            ledger_transactions: List of candidate ledger transactions
            threshold: Minimum similarity threshold
        
        Returns:
            Tuple of (matched_transaction, similarity_score) or None
        """
        if not ledger_transactions:
            return None
        
        # Find similar transactions
        similar = self.find_similar(
            bank_tx.description,
            ledger_transactions,
            top_k=1,
            threshold=threshold
        )
        
        if similar:
            return similar[0]
        
        return None

