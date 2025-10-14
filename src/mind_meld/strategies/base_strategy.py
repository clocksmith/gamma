"""Base class for Mind Meld swap strategies."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import numpy as np


@dataclass
class SwapDecision:
    """Decision about whether to swap models."""
    should_swap: bool
    reason: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SwapStrategyBase(ABC):
    """Base class for all swap strategies."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.swap_count = 0
        self.token_count = 0
        self.history: List[Dict[str, Any]] = []

    @abstractmethod
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
        Determine if models should swap.

        Args:
            token_text: The token that was just generated
            logits: Raw logits from the model
            current_model_idx: Index of current active model
            num_models: Total number of models in ensemble
            context: Current generation context
            **kwargs: Strategy-specific parameters

        Returns:
            SwapDecision with swap decision and metadata
        """
        pass

    def reset(self):
        """Reset strategy state."""
        self.swap_count = 0
        self.token_count = 0
        self.history = []

    def update_history(self, token_text: str, metadata: Dict[str, Any]):
        """Update generation history."""
        self.token_count += 1
        self.history.append({
            'token': token_text,
            'token_idx': self.token_count,
            'metadata': metadata
        })

        # Keep history bounded
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics."""
        return {
            'swap_count': self.swap_count,
            'token_count': self.token_count,
            'swap_rate': self.swap_count / max(self.token_count, 1)
        }

    def _log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"[{self.__class__.__name__}] {message}")


class FixedIntervalStrategy(SwapStrategyBase):
    """Swap every N tokens."""

    def __init__(self, interval: int = 5, verbose: bool = False):
        super().__init__(verbose)
        self.interval = interval
        self.counter = 0

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        self.counter += 1

        if self.counter >= self.interval:
            self.counter = 0
            self.swap_count += 1
            self._log(f"Fixed interval ({self.interval} tokens) reached")
            return SwapDecision(
                should_swap=True,
                reason=f"Fixed interval of {self.interval} tokens reached",
                metadata={'interval': self.interval}
            )

        return SwapDecision(should_swap=False, reason="Interval not reached")

    def reset(self):
        super().reset()
        self.counter = 0


class PatternBasedStrategy(SwapStrategyBase):
    """Swap at punctuation marks and natural boundaries."""

    def __init__(self, patterns: Optional[List[str]] = None, verbose: bool = False):
        super().__init__(verbose)
        self.patterns = patterns or ['.', '!', '?', '\n', ';', ':', ',']

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        for pattern in self.patterns:
            if pattern in token_text:
                self.swap_count += 1
                self._log(f"Pattern '{pattern}' detected in token '{token_text}'")
                return SwapDecision(
                    should_swap=True,
                    reason=f"Pattern '{pattern}' detected",
                    metadata={'pattern': pattern, 'token': token_text}
                )

        return SwapDecision(should_swap=False, reason="No pattern match")


class RoundRobinStrategy(SwapStrategyBase):
    """Swap every token (strict alternation)."""

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        self.swap_count += 1
        self._log("Round-robin swap")
        return SwapDecision(
            should_swap=True,
            reason="Round-robin alternation",
            confidence=1.0
        )


class RandomStrategy(SwapStrategyBase):
    """Swap with random probability."""

    def __init__(self, probability: float = 0.3, verbose: bool = False):
        super().__init__(verbose)
        self.probability = probability

    def should_swap(
        self,
        token_text: str,
        logits: np.ndarray,
        current_model_idx: int,
        num_models: int,
        context: str = "",
        **kwargs
    ) -> SwapDecision:
        if np.random.random() < self.probability:
            self.swap_count += 1
            self._log(f"Random swap (p={self.probability})")
            return SwapDecision(
                should_swap=True,
                reason=f"Random swap (probability={self.probability})",
                metadata={'probability': self.probability}
            )

        return SwapDecision(should_swap=False, reason="Random threshold not met")
