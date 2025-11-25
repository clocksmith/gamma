"""
GAMMA Type Definitions

This module provides type aliases and protocols for type checking across GAMMA.
Import from here for consistent typing throughout the codebase.
"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

import numpy as np
import numpy.typing as npt

# Basic token types
TokenId = int
TokenText = str
TokenIds = Union[List[TokenId], npt.NDArray[np.int64], Any]

# Attention and masks
AttentionMask = Optional[Union[List[int], npt.NDArray[np.int64], Any]]
AttentionWeights = Optional[Union[npt.NDArray[np.float32], Any]]

# Logits and probabilities
Logits = Union[npt.NDArray[np.float32], Any]
Probabilities = Union[npt.NDArray[np.float32], Any]

# KV Cache (can be various types depending on engine)
KVCache = Any

# Model output types
PredictionResult = Dict[str, Any]
EncodingResult = Tuple[TokenIds, AttentionMask]


@runtime_checkable
class TokenizerProtocol(Protocol):
    """Protocol for tokenizer interface that all engines must support."""

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Encode text to token IDs."""
        ...

    def decode(self, token_ids: List[int], skip_special_tokens: bool = False) -> str:
        """Decode token IDs to text."""
        ...

    def get_vocab(self) -> Dict[str, int]:
        """Get vocabulary as token -> ID mapping."""
        ...

    @property
    def eos_token_id(self) -> Optional[int]:
        """End of sequence token ID."""
        ...

    @property
    def bos_token_id(self) -> Optional[int]:
        """Beginning of sequence token ID."""
        ...

    @property
    def pad_token_id(self) -> Optional[int]:
        """Padding token ID."""
        ...


@runtime_checkable
class ModelProtocol(Protocol):
    """Protocol for model interface."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Forward pass."""
        ...


# Type variables for generic functions
TensorT = TypeVar('TensorT')
EngineT = TypeVar('EngineT', bound='LLMEngine')

# Configuration types
EngineConfig = Dict[str, Any]
SamplingConfig = Dict[str, Union[float, int, bool]]

# Mind Meld specific types
ModelIndex = int
SwapDecision = bool
BlendWeights = npt.NDArray[np.float32]


# Forward reference for LLMEngine (to avoid circular imports)
class LLMEngine(Protocol):
    """Protocol for LLM Engine interface."""

    model_name: str
    tokenizer: Any
    model: Any

    def load(self) -> None: ...
    def encode(self, text: str, add_special_tokens: bool = True) -> EncodingResult: ...
    def decode(self, token_ids: TokenIds, skip_special_tokens: bool = False) -> str: ...
    def predict_next(
        self,
        input_ids: TokenIds,
        attention_mask: AttentionMask,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> PredictionResult: ...
    def reset_kv_cache(self) -> None: ...
    def get_kv_cache(self) -> Optional[KVCache]: ...


__all__ = [
    # Basic types
    'TokenId',
    'TokenText',
    'TokenIds',
    # Attention types
    'AttentionMask',
    'AttentionWeights',
    # Logits/probabilities
    'Logits',
    'Probabilities',
    # KV Cache
    'KVCache',
    # Result types
    'PredictionResult',
    'EncodingResult',
    # Protocols
    'TokenizerProtocol',
    'ModelProtocol',
    'LLMEngine',
    # Type variables
    'TensorT',
    'EngineT',
    # Config types
    'EngineConfig',
    'SamplingConfig',
    # Mind Meld types
    'ModelIndex',
    'SwapDecision',
    'BlendWeights',
]
