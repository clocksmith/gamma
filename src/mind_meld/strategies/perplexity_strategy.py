"""Perplexity-based swap strategy - swap when model is uncertain."""

import numpy as np
from typing import Any, Dict, Optional
from collections import deque

from src.engines import sampling_utils
from .base_strategy import SwapStrategyBase, SwapDecision


class PerplexitySwapStrategy(SwapStrategyBase):
    """
    Swap when model perplexity exceeds threshold (model is uncertain).

    Perplexity measures how "surprised" a model is by its own prediction.
    High perplexity = high uncertainty = good time to swap to another model.
    """

    def __init__(
        self,
        threshold: float = 50.0,
        window_size: int = 5,
        adaptive: bool = True,
        verbose: bool = False
    ):
        """
        Initialize perplexity strategy.

        Args:
            threshold: Perplexity threshold for swapping
            window_size: Window size for smoothing perplexity
            adaptive: Adjust threshold based on recent history
            verbose: Enable verbose logging
        """
        super().__init__(verbose)
        self.threshold = threshold
        self.initial_threshold = threshold
        self.window_size = window_size
        self.adaptive = adaptive
        self.perplexity_history = deque(maxlen=window_size)
        self.min_perplexity = float('inf')
        self.max_perplexity = 0.0

    def calculate_perplexity(self, logits: np.ndarray, token_id: Optional[int] = None) -> float:
        """
        Calculate perplexity for the prediction.

        Perplexity = 2^(-log2(probability))
        Lower perplexity = more confident prediction
        Higher perplexity = more uncertain prediction

        Args:
            logits: Raw logits from model
            token_id: The token that was selected (if None, uses argmax)

        Returns:
            Perplexity value
        """
        # Handle NaN/inf in logits
        logits = sampling_utils.sanitize_logits(logits)

        # Convert to probabilities using stable softmax
        logits_shifted = logits - np.max(logits)
        exp_logits = np.exp(logits_shifted)
        probs = exp_logits / np.sum(exp_logits)

        # Get probability of selected token
        if token_id is None:
            token_id = np.argmax(probs)

        token_prob = probs[token_id] if token_id < len(probs) else 1e-10

        # Avoid log(0)
        token_prob = max(token_prob, 1e-10)

        # Calculate perplexity
        perplexity = 1.0 / token_prob

        return perplexity

    def calculate_entropy(self, logits: np.ndarray) -> float:
        """
        Calculate entropy of the probability distribution.
        Higher entropy = more uncertain.

        Args:
            logits: Raw logits from model

        Returns:
            Entropy value
        """
        # Convert to probabilities
        logits = sampling_utils.sanitize_logits(logits)
        logits_shifted = logits - np.max(logits)
        exp_logits = np.exp(logits_shifted)
        probs = exp_logits / np.sum(exp_logits)

        # Calculate entropy: -sum(p * log(p))
        # Avoid log(0)
        probs = np.clip(probs, 1e-10, 1.0)
        entropy = -np.sum(probs * np.log2(probs))

        return entropy

    def get_smoothed_perplexity(self) -> Optional[float]:
        """Get smoothed perplexity over recent history."""
        if not self.perplexity_history:
            return None
        return np.mean(self.perplexity_history)

    def update_adaptive_threshold(self):
        """Update threshold based on observed perplexity range."""
        if not self.adaptive or len(self.perplexity_history) < self.window_size:
            return

        # Set threshold to 75th percentile of observed perplexities
        perplexities = list(self.perplexity_history)
        self.threshold = np.percentile(perplexities, 75)

        # Don't drift too far from initial threshold
        self.threshold = np.clip(
            self.threshold,
            self.initial_threshold * 0.5,
            self.initial_threshold * 2.0
        )

        self._log(f"Adaptive threshold updated to {self.threshold:.2f}")

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        token_id: Optional[int] = None,
        **kwargs
    ) -> SwapDecision:
        """
        Determine if swap should occur based on perplexity.

        Args:
            token_text: Generated token text
            logits: Raw logits from model
            current_model_idx: Current model index
            num_models: Total models in ensemble
            context: Current context
            token_id: ID of generated token
            **kwargs: Additional parameters

        Returns:
            SwapDecision with swap decision and metadata
        """
        # Calculate perplexity
        perplexity = self.calculate_perplexity(logits, token_id)
        entropy = self.calculate_entropy(logits)

        # Update history
        self.perplexity_history.append(perplexity)
        self.min_perplexity = min(self.min_perplexity, perplexity)
        self.max_perplexity = max(self.max_perplexity, perplexity)

        # Update adaptive threshold
        if self.token_count % 10 == 0:  # Update every 10 tokens
            self.update_adaptive_threshold()

        # Get smoothed perplexity
        smoothed = self.get_smoothed_perplexity()
        use_perplexity = smoothed if smoothed is not None else perplexity

        # Update metadata
        metadata = {
            'perplexity': float(perplexity),
            'smoothed_perplexity': float(use_perplexity) if smoothed else None,
            'entropy': float(entropy),
            'threshold': float(self.threshold),
            'min_perplexity': float(self.min_perplexity),
            'max_perplexity': float(self.max_perplexity)
        }

        self.update_history(token_text, metadata)

        # Decide whether to swap
        if use_perplexity > self.threshold:
            self.swap_count += 1
            reason = f"High perplexity ({use_perplexity:.2f} > {self.threshold:.2f})"
            self._log(f"{reason} - model is uncertain, swapping")

            return SwapDecision(
                should_swap=True,
                reason=reason,
                confidence=min(use_perplexity / self.threshold, 1.0),
                metadata=metadata
            )

        return SwapDecision(
            should_swap=False,
            reason=f"Perplexity below threshold ({use_perplexity:.2f} <= {self.threshold:.2f})",
            confidence=self.threshold / max(use_perplexity, 1.0),
            metadata=metadata
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics."""
        base_stats = super().get_stats()

        avg_perplexity = np.mean(self.perplexity_history) if self.perplexity_history else 0.0

        return {
            **base_stats,
            'avg_perplexity': float(avg_perplexity),
            'min_perplexity': float(self.min_perplexity) if self.min_perplexity != float('inf') else 0.0,
            'max_perplexity': float(self.max_perplexity),
            'current_threshold': float(self.threshold),
            'adaptive': self.adaptive
        }

    def reset(self):
        """Reset strategy state."""
        super().reset()
        self.perplexity_history.clear()
        self.min_perplexity = float('inf')
        self.max_perplexity = 0.0
        self.threshold = self.initial_threshold


class ConfidenceBasedStrategy(PerplexitySwapStrategy):
    """
    Swap when model confidence drops below threshold.
    Confidence is inverse of perplexity (normalized).
    """

    def __init__(
        self,
        min_confidence: float = 0.3,
        window_size: int = 5,
        adaptive: bool = True,
        verbose: bool = False
    ):
        """
        Initialize confidence-based strategy.

        Args:
            min_confidence: Minimum confidence threshold (0-1)
            window_size: Window for smoothing
            adaptive: Enable adaptive threshold
            verbose: Enable verbose logging
        """
        # Convert confidence to perplexity threshold
        # confidence = 1 / perplexity (normalized)
        # So perplexity = 1 / confidence
        perplexity_threshold = 1.0 / max(min_confidence, 0.01)

        super().__init__(
            threshold=perplexity_threshold,
            window_size=window_size,
            adaptive=adaptive,
            verbose=verbose
        )
        self.min_confidence = min_confidence

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        token_id: Optional[int] = None,
        **kwargs
    ) -> SwapDecision:
        """Determine swap based on confidence (inverse perplexity)."""
        decision = super().should_swap(
            token_text, logits, current_model_idx, num_models,
            context, token_id, **kwargs
        )

        # Add confidence to metadata
        perplexity = decision.metadata['perplexity']
        confidence = 1.0 / max(perplexity, 1.0)
        decision.metadata['confidence'] = float(confidence)

        # Update reason to talk about confidence instead of perplexity
        if decision.should_swap:
            decision.reason = f"Low confidence ({confidence:.3f} < {self.min_confidence:.3f})"
        else:
            decision.reason = f"Sufficient confidence ({confidence:.3f} >= {self.min_confidence:.3f})"

        return decision
