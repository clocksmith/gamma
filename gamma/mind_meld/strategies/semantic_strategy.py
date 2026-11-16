"""Semantic similarity-based swap strategy - swap on context drift."""

import numpy as np
from typing import Any, Dict, Optional
from collections import deque

from .base_strategy import SwapStrategyBase, SwapDecision


class SemanticSimilarityStrategy(SwapStrategyBase):
    """
    Swap when semantic drift is detected.

    Uses simple embedding-based similarity to detect topic/context shifts.
    Falls back to word overlap if embeddings aren't available.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        window_size: int = 50,
        update_interval: int = 10,
        use_embeddings: bool = True,
        verbose: bool = False
    ):
        """
        Initialize semantic similarity strategy.

        Args:
            similarity_threshold: Minimum similarity to maintain (0-1)
            window_size: Context window size for comparison
            update_interval: Update reference context every N tokens
            use_embeddings: Try to use sentence embeddings
            verbose: Enable verbose logging
        """
        super().__init__(verbose)
        self.similarity_threshold = similarity_threshold
        self.window_size = window_size
        self.update_interval = update_interval
        self.use_embeddings = use_embeddings

        # Context tracking
        self.reference_context = ""
        self.current_window = deque(maxlen=window_size)
        self.reference_embedding = None

        # Try to load embedding model
        self.embedder = None
        if use_embeddings:
            self._init_embedder()

    def _init_embedder(self):
        """Initialize sentence embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self._log("Loaded sentence-transformers model")
        except ImportError:
            self._log("sentence-transformers not available, falling back to word overlap")
            self.use_embeddings = False
        except Exception as e:
            self._log(f"Failed to load embedder: {e}, falling back to word overlap")
            self.use_embeddings = False

    def _embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        if self.embedder is not None and len(text.strip()) > 0:
            try:
                return self.embedder.encode(text, show_progress_bar=False)
            except Exception as e:
                self._log(f"Embedding failed: {e}")
                return None
        return None

    def _calculate_embedding_similarity(self, text1: str, text2: str) -> Optional[float]:
        """Calculate cosine similarity between two texts using embeddings."""
        if not self.embedder or not text1.strip() or not text2.strip():
            return None

        try:
            emb1 = self._embed_text(text1)
            emb2 = self._embed_text(text2)

            if emb1 is None or emb2 is None:
                return None

            # Cosine similarity
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2)
            )
            return float(similarity)
        except Exception as e:
            self._log(f"Similarity calculation failed: {e}")
            return None

    def _calculate_word_overlap(self, text1: str, text2: str) -> float:
        """Calculate word overlap similarity (fallback method)."""
        if not text1.strip() or not text2.strip():
            return 1.0

        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 1.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if self.use_embeddings:
            sim = self._calculate_embedding_similarity(text1, text2)
            if sim is not None:
                return sim

        # Fallback to word overlap
        return self._calculate_word_overlap(text1, text2)

    def update_reference_context(self, context: str):
        """Update the reference context for comparison."""
        self.reference_context = context
        if self.use_embeddings and self.embedder:
            self.reference_embedding = self._embed_text(context)
        self._log(f"Updated reference context ({len(context)} chars)")

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        """
        Determine if swap should occur based on semantic drift.

        Args:
            token_text: Generated token text
            logits: Raw logits (not used in this strategy)
            current_model_idx: Current model index
            num_models: Total models
            context: Current full context
            **kwargs: Additional parameters

        Returns:
            SwapDecision with swap decision and metadata
        """
        # Add token to window
        self.current_window.append(token_text)
        current_window_text = ''.join(self.current_window)

        # Initialize reference on first token
        if self.token_count == 0:
            self.update_reference_context(context if context else token_text)

        # Update reference context periodically
        if self.token_count > 0 and self.token_count % self.update_interval == 0:
            # Use recent window as new reference
            self.update_reference_context(current_window_text)

        # Calculate similarity between current window and reference
        similarity = self._calculate_similarity(current_window_text, self.reference_context)

        metadata = {
            'similarity': float(similarity),
            'threshold': float(self.similarity_threshold),
            'window_size': len(self.current_window),
            'reference_length': len(self.reference_context),
            'method': 'embedding' if self.use_embeddings else 'word_overlap'
        }

        self.update_history(token_text, metadata)

        # Decide whether to swap based on similarity
        if similarity < self.similarity_threshold:
            self.swap_count += 1
            reason = f"Semantic drift detected (similarity: {similarity:.3f} < {self.similarity_threshold:.3f})"
            self._log(reason)

            # Update reference to current context (we've drifted to a new topic)
            self.update_reference_context(current_window_text)

            return SwapDecision(
                should_swap=True,
                reason=reason,
                confidence=1.0 - similarity,  # Lower similarity = higher confidence in swap
                metadata=metadata
            )

        return SwapDecision(
            should_swap=False,
            reason=f"Context stable (similarity: {similarity:.3f} >= {self.similarity_threshold:.3f})",
            confidence=similarity,
            metadata=metadata
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics."""
        base_stats = super().get_stats()

        # Calculate average similarity from history
        similarities = [h['metadata'].get('similarity', 0) for h in self.history if 'metadata' in h]
        avg_similarity = np.mean(similarities) if similarities else 0.0

        return {
            **base_stats,
            'avg_similarity': float(avg_similarity),
            'threshold': float(self.similarity_threshold),
            'uses_embeddings': self.use_embeddings,
            'reference_length': len(self.reference_context)
        }

    def reset(self):
        """Reset strategy state."""
        super().reset()
        self.reference_context = ""
        self.current_window.clear()
        self.reference_embedding = None


class SyntacticRoleStrategy(SwapStrategyBase):
    """
    Swap based on syntactic/grammatical role of tokens.

    Example: Use creative model for adjectives, technical model for nouns.
    """

    def __init__(
        self,
        role_mapping: Optional[Dict[str, int]] = None,
        verbose: bool = False
    ):
        """
        Initialize syntactic role strategy.

        Args:
            role_mapping: Map of POS tags to model indices
            verbose: Enable verbose logging
        """
        super().__init__(verbose)
        self.role_mapping = role_mapping or {
            'ADJ': 0,  # Adjectives -> Model 0 (creative)
            'NOUN': 1,  # Nouns -> Model 1 (technical)
            'VERB': 0,  # Verbs -> Model 0 (creative)
        }
        self.tagger = None
        self._init_tagger()

    def _init_tagger(self):
        """Initialize POS tagger."""
        try:
            import spacy
            try:
                self.tagger = spacy.load("en_core_web_sm")
                self._log("Loaded spaCy POS tagger")
            except OSError:
                self._log("spaCy model not found, strategy will not work")
                self._log("Run: python -m spacy download en_core_web_sm")
        except ImportError:
            self._log("spaCy not available, strategy will not work")
            self._log("Install with: pip install spacy")

    def _get_pos_tag(self, token_text: str, context: str = "") -> Optional[str]:
        """Get POS tag for a token."""
        if not self.tagger:
            return None

        try:
            # Analyze in context if available
            text_to_analyze = f"{context} {token_text}".strip()
            doc = self.tagger(text_to_analyze)

            if len(doc) > 0:
                # Get last token's POS tag
                return doc[-1].pos_
        except Exception as e:
            self._log(f"POS tagging failed: {e}")

        return None

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        """Determine swap based on token's syntactic role."""
        if not self.tagger:
            return SwapDecision(
                should_swap=False,
                reason="POS tagger not available"
            )

        pos_tag = self._get_pos_tag(token_text, context)

        metadata = {
            'pos_tag': pos_tag,
            'token': token_text
        }

        self.update_history(token_text, metadata)

        if pos_tag and pos_tag in self.role_mapping:
            target_model = self.role_mapping[pos_tag]

            if target_model != current_model_idx:
                self.swap_count += 1
                reason = f"POS tag '{pos_tag}' maps to model {target_model}"
                self._log(reason)

                return SwapDecision(
                    should_swap=True,
                    reason=reason,
                    confidence=1.0,
                    metadata={**metadata, 'target_model': target_model}
                )

        return SwapDecision(
            should_swap=False,
            reason=f"POS tag '{pos_tag}' doesn't require swap",
            metadata=metadata
        )
