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
from dataclasses import dataclass, field, fields

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
@dataclass
class PredictionResult:
    """Typed prediction result returned by engines."""

    next_token_id: int
    logits_raw: Any = None
    logits_processed: Any = None
    logits_after_temperature: Any = None
    logits_after_top_k: Any = None
    logits_after_top_p: Any = None
    probabilities_raw: Any = None
    probabilities_temp: Any = None
    probabilities_top_k: Any = None
    probabilities_processed: Any = None
    top_tokens_processed: Optional[List[str]] = None
    top_probs_processed: Optional[List[float]] = None
    top_token_ids_processed: Optional[List[int]] = None
    attention: Any = None
    hidden_states: Any = None
    forward_time: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredictionResult":
        """Create a PredictionResult from a legacy dict."""
        known_fields = {f.name for f in fields(cls) if f.name != "extra"}
        init = {k: data.get(k) for k in known_fields if k in data}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        if "next_token_id" not in init:
            raise KeyError("PredictionResult requires next_token_id")
        init["extra"] = extra
        return cls(**init)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like getter for compatibility."""
        if hasattr(self, key):
            value = getattr(self, key)
            return default if value is None else value
        return self.extra.get(key, default)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            value = getattr(self, key)
            if value is None:
                raise KeyError(key)
            return value
        if key in self.extra:
            return self.extra[key]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        if hasattr(self, key):
            return getattr(self, key) is not None
        return key in self.extra

    def keys(self) -> List[str]:
        keys = []
        for f in fields(self):
            if f.name == "extra":
                continue
            if getattr(self, f.name) is not None:
                keys.append(f.name)
        keys.extend(self.extra.keys())
        return keys

    def items(self):
        return self.to_dict().items()

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for f in fields(self):
            if f.name == "extra":
                continue
            value = getattr(self, f.name)
            if value is not None:
                data[f.name] = value
        data.update(self.extra)
        return data


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

    @property
    def unk_token_id(self) -> Optional[int]:
        """Unknown token ID."""
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
