"""
GAMMA Engine Interface

This module defines the abstract base class for all LLM inference engines.
All engines must implement this interface to work with GAMMA.
"""

from abc import ABC, abstractmethod
import logging
from typing import (
    List,
    Tuple,
    Optional,
    Dict,
    Any,
    Union,
    Callable,
    TypeVar,
    Protocol,
    runtime_checkable,
)
from enum import Enum

import numpy as np
import numpy.typing as npt

from src.core import config as cfg

logger = logging.getLogger(__name__)

# Type aliases for clarity
TokenId = int
TokenIds = Union[List[TokenId], npt.NDArray[np.int64], Any]  # Any for tensor types
AttentionMask = Optional[Union[List[int], npt.NDArray[np.int64], Any]]
Logits = Union[npt.NDArray[np.float32], Any]
Probabilities = Union[npt.NDArray[np.float32], Any]
KVCache = Any  # KV cache can be various types depending on engine


@runtime_checkable
class TokenizerProtocol(Protocol):
    """Protocol for tokenizer interface."""

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]: ...
    def decode(self, token_ids: List[int], skip_special_tokens: bool = False) -> str: ...
    def get_vocab(self) -> Dict[str, int]: ...

    @property
    def eos_token_id(self) -> Optional[int]: ...
    @property
    def bos_token_id(self) -> Optional[int]: ...
    @property
    def pad_token_id(self) -> Optional[int]: ...
    @property
    def unk_token_id(self) -> Optional[int]: ...


# Type variable for tensor types
TensorT = TypeVar('TensorT')


class TokenCategory(Enum):
    WORD = "word"
    PUNCTUATION = "punctuation"
    SPECIAL = "special"
    WHITESPACE = "whitespace"
    NUMBER = "number"
    OTHER = "other"


class LLMEngine(ABC):
    def __init__(
        self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.engine_config = engine_specific_config or {}
        self.model: Any = None
        self.tokenizer: Any = None
        self._special_token_id_to_game_repr: Dict[int, str] = {}
        self._token_cache: Dict[int, str] = {}
        self._kv_cache: Any = None

    # Configuration helper methods (reduces duplication across engines)
    def get_trust_remote_code(self) -> bool:
        """Get trust_remote_code setting."""
        return self.engine_config.get("trust_remote_code", False)

    def get_hf_token(self) -> Optional[str]:
        """Get HuggingFace token."""
        return self.engine_config.get("hf_token", None)

    def get_verbose(self) -> bool:
        """Get verbose logging setting."""
        return self.engine_config.get("verbose", False)

    def get_max_tokens_for_display(self) -> int:
        """Get max tokens to display in probability output."""
        return self.engine_config.get("max_tokens_for_prob_display", 10)

    def get_use_kv_cache(self) -> bool:
        """Get KV cache usage setting."""
        return self.engine_config.get("use_kv_cache", True)

    def get_seed(self) -> Optional[int]:
        """Get random seed for reproducibility."""
        return self.engine_config.get("seed", None)

    def get_device_map(self, default: str = "auto") -> str:
        """Get device map configuration (for HF transformers)."""
        return self.engine_config.get("device_map", default)

    def get_low_cpu_mem_usage(self) -> bool:
        """Get low CPU memory usage setting."""
        return self.engine_config.get("low_cpu_mem_usage", True)

    # Error handling helpers (Phase 2.2 - reduces duplication)
    def _error_model_not_loaded(self) -> RuntimeError:
        """Create standardized 'model not loaded' error."""
        engine_name = self.__class__.__name__
        return RuntimeError(f"{engine_name}: Model not loaded. Call load() first.")

    def _error_tokenizer_not_loaded(self) -> RuntimeError:
        """Create standardized 'tokenizer not loaded' error."""
        engine_name = self.__class__.__name__
        return RuntimeError(f"{engine_name}: Tokenizer not loaded.")

    def _ensure_model_loaded(self):
        """Ensure model is loaded, raise error if not."""
        if not self.model:
            raise self._error_model_not_loaded()

    def _ensure_tokenizer_loaded(self):
        """Ensure tokenizer is loaded, raise error if not."""
        if not self.tokenizer:
            raise self._error_tokenizer_not_loaded()

    @abstractmethod
    def load(self) -> None:
        """Load the model and tokenizer into memory."""
        pass

    @abstractmethod
    def encode(
        self, text: str, add_special_tokens: bool = True
    ) -> Tuple[TokenIds, AttentionMask]:
        """
        Encode text to token IDs.

        Args:
            text: Input text to encode
            add_special_tokens: Whether to add special tokens (BOS, EOS, etc.)

        Returns:
            Tuple of (input_ids, attention_mask)
        """
        pass

    @abstractmethod
    def decode(self, token_ids: TokenIds, skip_special_tokens: bool = False) -> str:
        """
        Decode token IDs back to text.

        Args:
            token_ids: Token IDs to decode
            skip_special_tokens: Whether to skip special tokens in output

        Returns:
            Decoded text string
        """
        pass

    @abstractmethod
    def predict_next(
        self,
        input_ids: TokenIds,
        attention_mask: AttentionMask,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        """
        Predict the next token given input IDs.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask for the input
            temperature: Sampling temperature (higher = more random)
            top_k: Limit to top-k tokens (0 = disabled)
            top_p: Nucleus sampling threshold (1.0 = disabled)
            output_attentions: Whether to return attention weights
            output_hidden_states: Whether to return hidden states

        Returns:
            Dictionary containing at minimum:
                - next_token_id: ID of the predicted next token
                - logits_raw: Raw logits from the model
                - probabilities: Processed probability distribution
        """
        pass

    def reset_kv_cache(self) -> None:
        """Reset the KV cache to force full recomputation."""
        self._kv_cache = None

    def _process_logits_common_pipeline(
        self,
        logits_np: np.ndarray,
        temperature: float,
        top_k: int,
        top_p: float
    ) -> Dict[str, Any]:
        """
        Common sampling pipeline logic shared across all engines.

        This consolidates the repeated pattern of:
        1. Processing logits through temperature/top-k/top-p
        2. Computing probabilities
        3. Selecting next token
        4. Getting top-k tokens for display

        Reduces ~50 lines of duplicate code per engine.

        Args:
            logits_np: Raw logits as numpy array (shape: [vocab_size] or [1, vocab_size])
            temperature: Sampling temperature
            top_k: Top-K filtering
            top_p: Top-P (nucleus) filtering

        Returns:
            Dictionary containing:
                - next_token_id: Selected next token ID
                - logits_processed_np: Processed logits (numpy)
                - logits_temp_np: After temperature (numpy)
                - logits_topk_np: After top-k filtering (numpy)
                - probs_processed_np: Final probabilities (numpy)
                - top_tokens: List of top token texts
                - top_probs: List of top token probabilities
        """
        from src.engines import sampling_utils

        # Process logits through sampling pipeline
        logits_proc_np, logits_temp_np, logits_k_np = sampling_utils.process_logits_pipeline(
            logits_np, temperature, top_k, top_p, return_intermediates=True
        )

        # Compute probabilities
        probs_proc_np = sampling_utils.softmax(logits_proc_np)

        # Select next token
        next_token_id = int(np.argmax(probs_proc_np, axis=-1))

        # Get top-k tokens for display
        max_display_k = max(
            top_k if top_k > 0 else 1,
            cfg.MAX_TOKENS_FOR_PROB_DISPLAY,
            1
        )
        top_tokens, top_probs, _ = sampling_utils.get_top_k_tokens(
            logits_proc_np,
            max_display_k,
            self.get_token_text,
            is_probs=False
        )

        return {
            "next_token_id": next_token_id,
            "logits_processed_np": logits_proc_np,
            "logits_temp_np": logits_temp_np,
            "logits_topk_np": logits_k_np,
            "probs_processed_np": probs_proc_np,
            "top_tokens": top_tokens,
            "top_probs": top_probs
        }

    def _load_hf_tokenizer(self, model_name: Optional[str] = None, **kwargs):
        """
        Load HuggingFace tokenizer with common configuration.

        Consolidates duplicate tokenizer loading code across engines.

        Args:
            model_name: Model name/path for tokenizer. If None, uses self.model_name
            **kwargs: Additional keyword arguments to pass to AutoTokenizer.from_pretrained()
                      (e.g., use_fast=True, padding_side="left", etc.)

        Raises:
            RuntimeError: If tokenizer loading fails
        """
        from transformers import AutoTokenizer

        model_name = model_name or self.model_name
        trust_remote = self.get_trust_remote_code()
        token = self.get_hf_token()
        engine_name = self.__class__.__name__

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, trust_remote_code=trust_remote, token=token, **kwargs
            )
        except Exception as e:
            raise RuntimeError(
                f"{engine_name}: Tokenizer load failed for '{model_name}': {e}"
            ) from e

    @abstractmethod
    def get_vocabulary_size(self) -> int:
        pass

    def get_token_text(self, token_id: int) -> str:
        """Get text representation of a token ID.

        This method handles caching and special tokens, delegating to
        _decode_token_raw() for engine-specific decoding logic.
        """
        # Check cache first
        if token_id in self._token_cache:
            return self._token_cache[token_id]

        # Check if it's a special token
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr:
            self._token_cache[token_id] = game_repr
            return game_repr

        # Check tokenizer is loaded
        if not self.tokenizer:
            engine_name = self.__class__.__name__
            raise RuntimeError(f"{engine_name}: Tokenizer not loaded.")

        # Decode using engine-specific logic
        try:
            token_text = self._decode_token_raw(token_id)
            if not token_text:
                token_text = f"<ID:{token_id}>"
        except Exception:
            token_text = f"<DecodeErr:{token_id}>"

        # Cache and return
        self._token_cache[token_id] = token_text
        return token_text

    def _decode_token_hf_common(self, token_id: int) -> str:
        """
        Common HuggingFace tokenizer decoding logic.

        Handles common patterns across HF-based engines:
        - convert_ids_to_tokens() with bytes decoding
        - SentencePiece underscore/space handling
        - Fallback to full decode for empty tokens

        Engines using HF tokenizers can call this to reduce duplication.
        """
        if not self.tokenizer:
            return f"<token_{token_id}>"

        try:
            # Get token text from tokenizer
            token_text = self.tokenizer.convert_ids_to_tokens([token_id])[0]

            # Handle bytes encoding
            if isinstance(token_text, bytes):
                token_text = token_text.decode("utf-8", errors="replace")

            # Handle SentencePiece prefix (space or underscore)
            if hasattr(self.tokenizer, "sp_model"):
                if token_text.startswith("▁"):
                    token_text = token_text[1:] or " "
                elif token_text.startswith(" "):
                    token_text = token_text[1:]

            # Fallback for empty tokens
            if not token_text:
                decoded_raw = self.tokenizer.decode([token_id], skip_special_tokens=False)
                token_text = decoded_raw.strip() if decoded_raw and decoded_raw != getattr(self.tokenizer, 'unk_token', None) else ""

            return token_text
        except Exception:
            return f"<token_{token_id}>"

    @abstractmethod
    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID to its text representation.

        Engine-specific implementation. Should return the raw token text
        without caching or special token handling.

        Engines using HuggingFace tokenizers can call self._decode_token_hf_common()
        to use the standard HF decoding logic.

        Raises:
            Exception: If decoding fails
        """
        pass

    def is_word_like_token(
        self, token_id: int, token_text: Optional[str] = None
    ) -> bool:
        if token_text is None:
            token_text = self.get_token_text(token_id)

        if token_text in cfg.SPECIAL_TOKEN_GAME_REPR.values():
            return False
        if not any(c.isalpha() for c in token_text):
            return False
        stripped_text = token_text.strip()
        if (
            len(stripped_text) < cfg.MIN_WORD_TOKEN_LENGTH
            and not stripped_text.isalpha()
        ):
            return False
        return True

    @abstractmethod
    def get_attention_for_visualization(
        self, attention_output: Any, input_ids_for_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        pass

    @abstractmethod
    def get_probabilities_at_step(
        self, logits_or_probs: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        pass

    def get_config_summary(self) -> Dict[str, Any]:
        """Get engine configuration summary for display."""
        base_config = {"engine_class": self.__class__.__name__}
        # Subclasses can override to add engine-specific config
        return {**base_config, **self.get_engine_specific_config()}
    
    def get_engine_specific_config(self) -> Dict[str, Any]:
        """Override in subclasses to provide engine-specific configuration."""
        return {}

    def _populate_special_token_map(self):
        if not self.tokenizer:
            logger.warning(
                f"{self.__class__.__name__}: Tokenizer not loaded, cannot populate special token map."
            )
            return

        for game_key, game_repr_str in cfg.SPECIAL_TOKEN_GAME_REPR.items():
            token_id_attr = f"{game_key}_id"
            token_id_val = getattr(self.tokenizer, token_id_attr, None)
            if token_id_val is not None:
                try:
                    if hasattr(token_id_val, "item") and callable(token_id_val.item):
                        token_id_val = token_id_val.item()
                    elif (
                        hasattr(token_id_val, "numpy")
                        and callable(token_id_val.numpy)
                        and hasattr(token_id_val.numpy(), "item")
                    ):
                        token_id_val = token_id_val.numpy().item()
                    token_id_int = int(token_id_val)
                    self._special_token_id_to_game_repr[token_id_int] = game_repr_str
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(
                        f"{self.__class__.__name__}: Could not convert/use token ID for '{game_key}': {token_id_val} (Error: {e})"
                    )

        nl_attrs = ["newline_token_id", "nl_token_id", "line_break_token_id"]
        for nl_attr in nl_attrs:
            newline_id_val = getattr(self.tokenizer, nl_attr, None)
            if newline_id_val is not None:
                try:
                    if hasattr(newline_id_val, "item") and callable(newline_id_val.item):
                        newline_id_val = newline_id_val.item()
                    newline_id_int = int(newline_id_val)
                    self._special_token_id_to_game_repr[newline_id_int] = cfg.TOKEN_NL
                    break
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(
                        f"{self.__class__.__name__}: Could not convert/use newline token ID from '{nl_attr}': {newline_id_val} (Error: {e})"
                    )

        if hasattr(self.tokenizer, "token_bos") and callable(self.tokenizer.token_bos):
            bos_id = self.tokenizer.token_bos()
            if isinstance(bos_id, int) and bos_id not in self._special_token_id_to_game_repr:
                self._special_token_id_to_game_repr[bos_id] = cfg.TOKEN_BOS
        if hasattr(self.tokenizer, "token_eos") and callable(self.tokenizer.token_eos):
            eos_id = self.tokenizer.token_eos()
            if isinstance(eos_id, int) and eos_id not in self._special_token_id_to_game_repr:
                self._special_token_id_to_game_repr[eos_id] = cfg.TOKEN_EOS
        if hasattr(self.tokenizer, "token_nl") and callable(self.tokenizer.token_nl):
            nl_id_direct = self.tokenizer.token_nl()
            if isinstance(nl_id_direct, int) and nl_id_direct not in self._special_token_id_to_game_repr:
                self._special_token_id_to_game_repr[nl_id_direct] = cfg.TOKEN_NL
    
    # New abstract methods for proper abstraction
    @abstractmethod
    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array."""
        pass
    
    @abstractmethod
    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert numpy array to engine-specific tensor."""
        pass
    
    @abstractmethod
    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate two tensors along specified dimension."""
        pass
    
    def get_eos_token_id(self) -> Optional[int]:
        """Get EOS token ID if available."""
        if hasattr(self.tokenizer, 'eos_token_id'):
            eos_id = self.tokenizer.eos_token_id
            if eos_id is not None:
                return int(eos_id) if not isinstance(eos_id, int) else eos_id
        return None
    
    def get_unk_token_id(self) -> Optional[int]:
        """Get UNK token ID if available."""
        if hasattr(self.tokenizer, 'unk_token_id'):
            unk_id = self.tokenizer.unk_token_id
            if unk_id is not None:
                return int(unk_id) if not isinstance(unk_id, int) else unk_id
        return None
    
    def get_pad_token_id(self) -> Optional[int]:
        """Get PAD token ID if available."""
        if hasattr(self.tokenizer, 'pad_token_id'):
            pad_id = self.tokenizer.pad_token_id
            if pad_id is not None:
                return int(pad_id) if not isinstance(pad_id, int) else pad_id
        return None
    
    def get_bos_token_id(self) -> Optional[int]:
        """Get BOS token ID if available."""
        if hasattr(self.tokenizer, 'bos_token_id'):
            bos_id = self.tokenizer.bos_token_id
            if bos_id is not None:
                return int(bos_id) if not isinstance(bos_id, int) else bos_id
        return None
    
    def get_special_tokens(self) -> Dict[str, Optional[int]]:
        """Get all special token IDs."""
        return {
            'eos': self.get_eos_token_id(),
            'unk': self.get_unk_token_id(),
            'pad': self.get_pad_token_id(),
            'bos': self.get_bos_token_id()
        }
    
    def is_special_token(self, token_id: int) -> bool:
        """Check if token is a special token."""
        return token_id in self._special_token_id_to_game_repr
    
    def get_token_category(self, token_id: int) -> TokenCategory:
        """Categorize a token."""
        if self.is_special_token(token_id):
            return TokenCategory.SPECIAL
        
        token_text = self.get_token_text(token_id)
        
        # Check for whitespace
        if token_text.strip() == "":
            return TokenCategory.WHITESPACE
        
        # Check for punctuation
        if all(c in ".,!?;:()[]{}'\"\\/-" for c in token_text.strip()):
            return TokenCategory.PUNCTUATION
        
        # Check for numbers
        if token_text.strip().replace('.', '').replace(',', '').isdigit():
            return TokenCategory.NUMBER
        
        # Check for word-like
        if self.is_word_like_token(token_id, token_text):
            return TokenCategory.WORD
        
        return TokenCategory.OTHER
    
    # KV Cache management abstractions
    def get_kv_cache(self) -> Any:
        """Get current KV cache."""
        return self._kv_cache
    
    def set_kv_cache(self, cache: Any):
        """Set KV cache."""
        self._kv_cache = cache
    
    def has_kv_cache(self) -> bool:
        """Check if KV cache exists."""
        return self._kv_cache is not None
    
    @abstractmethod
    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape if available."""
        pass
    
    @abstractmethod
    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        pass

    @abstractmethod
    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        pass

    def bridge_kv_cache_to(self, target_engine: 'LLMEngine') -> bool:
        """
        Attempt to bridge KV cache to another engine.

        Default implementation: KV cache bridging not supported.
        Engines that support bridging should override this method.
        """
        engine_name = self.__class__.__name__
        logger.debug(f"{engine_name}: KV cache bridging not supported")
        return False

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """
        Export KV cache state for bridging.

        Default implementation: Returns minimal metadata only.
        Engines that support full KV cache export should override this method.
        """
        return {
            'engine_type': self.__class__.__name__.replace('Engine', '').lower(),
            'model_name': self.model_name,
            'has_cache': self.has_kv_cache(),
            'cache_supported': False
        }

    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """
        Import KV cache state from another engine.

        Default implementation: KV cache import not supported.
        Engines that support importing should override this method.
        """
        engine_name = self.__class__.__name__
        logger.debug(f"{engine_name}: KV cache import not supported")
        return False
    
    @abstractmethod
    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids tensor."""
        pass
    
    @abstractmethod
    def get_device(self) -> str:
        """Get device type (cpu, cuda, mps, etc)."""
        pass

    # ========================================================================
    # KV Cache Validation & Metadata (standardized across engines)
    # ========================================================================

    def get_kv_cache_metadata(self) -> Optional[Dict[str, Any]]:
        """Get structured metadata about the current KV cache.

        Returns standardized metadata that can be used for validation
        and compatibility checking across different engine types.

        Returns:
            Dictionary with:
                - has_cache: bool - Whether cache exists
                - seq_len: int - Sequence length in cache
                - num_layers: int - Number of layers
                - shape: tuple - Cache shape if available
                - dtype: str - Data type
                - device: str - Device location
                - engine_type: str - Engine class name
                - supports_bridging: bool - Whether cache can be bridged
        """
        if not self.has_kv_cache():
            return {
                'has_cache': False,
                'seq_len': 0,
                'num_layers': 0,
                'shape': None,
                'dtype': None,
                'device': None,
                'engine_type': self.__class__.__name__,
                'supports_bridging': False
            }

        cache = self._kv_cache
        shape = self.get_kv_cache_shape()
        seq_len = self._infer_cache_seq_len(cache)
        dtype = self._infer_cache_dtype(cache)

        return {
            'has_cache': True,
            'seq_len': seq_len,
            'num_layers': self._infer_cache_layers(cache),
            'shape': shape,
            'dtype': dtype,
            'device': self._infer_cache_device(cache),
            'engine_type': self.__class__.__name__,
            'supports_bridging': self._supports_cache_bridging()
        }

    def _infer_cache_seq_len(self, cache: Any) -> int:
        """Infer sequence length from cache object."""
        if cache is None:
            return 0

        # Handle tuple of layer caches (HuggingFace format)
        if isinstance(cache, (list, tuple)) and len(cache) > 0:
            first_layer = cache[0]
            if isinstance(first_layer, (list, tuple)) and len(first_layer) >= 2:
                key_tensor = first_layer[0]
                if hasattr(key_tensor, 'shape'):
                    # Typical shape: (batch, num_heads, seq_len, head_dim)
                    return key_tensor.shape[-2] if len(key_tensor.shape) >= 2 else 0

        return 0

    def _infer_cache_layers(self, cache: Any) -> int:
        """Infer number of layers from cache object."""
        if cache is None:
            return 0

        if isinstance(cache, (list, tuple)):
            return len(cache)

        return 0

    def _infer_cache_dtype(self, cache: Any) -> Optional[str]:
        """Infer data type from cache object."""
        if cache is None:
            return None

        if isinstance(cache, (list, tuple)) and len(cache) > 0:
            first_layer = cache[0]
            if isinstance(first_layer, (list, tuple)) and len(first_layer) >= 2:
                key_tensor = first_layer[0]
                if hasattr(key_tensor, 'dtype'):
                    return str(key_tensor.dtype)

        return None

    def _infer_cache_device(self, cache: Any) -> Optional[str]:
        """Infer device from cache object."""
        if cache is None:
            return None

        if isinstance(cache, (list, tuple)) and len(cache) > 0:
            first_layer = cache[0]
            if isinstance(first_layer, (list, tuple)) and len(first_layer) >= 2:
                key_tensor = first_layer[0]
                if hasattr(key_tensor, 'device'):
                    return str(key_tensor.device)

        return self.get_device()

    def _supports_cache_bridging(self) -> bool:
        """Check if this engine supports KV cache bridging."""
        # Override in subclasses that support bridging
        return False

    def validate_cache_compatibility(
        self,
        target_engine: 'LLMEngine',
        required_seq_len: int = 0
    ) -> Tuple[bool, str]:
        """Validate if current cache is compatible with target engine.

        Args:
            target_engine: Engine to check compatibility with
            required_seq_len: Minimum sequence length required

        Returns:
            Tuple of (is_compatible, reason_if_not)
        """
        source_meta = self.get_kv_cache_metadata()
        if not source_meta or not source_meta.get('has_cache'):
            return False, "Source has no KV cache"

        if not self._supports_cache_bridging():
            return False, f"{self.__class__.__name__} does not support cache bridging"

        if not target_engine._supports_cache_bridging():
            return False, f"{target_engine.__class__.__name__} does not support cache import"

        # Check sequence length
        if source_meta['seq_len'] < required_seq_len:
            return False, f"Cache seq_len {source_meta['seq_len']} < required {required_seq_len}"

        # Check layer count compatibility
        source_layers = source_meta.get('num_layers', 0)
        try:
            target_layers = target_engine.get_num_layers()
        except (RuntimeError, AttributeError):
            target_layers = 0

        if source_layers != target_layers and source_layers > 0 and target_layers > 0:
            return False, f"Layer count mismatch: source={source_layers}, target={target_layers}"

        return True, "Compatible"

    def truncate_kv_cache(self, max_len: int) -> bool:
        """Truncate KV cache to specified sequence length.

        Default implementation does nothing (returns False).
        Override in engines that support cache truncation.

        Args:
            max_len: Maximum sequence length to keep

        Returns:
            True if truncation was successful
        """
        return False

    def extend_kv_cache(self, extension: Any) -> bool:
        """Extend KV cache with additional key-value pairs.

        Default implementation does nothing (returns False).
        Override in engines that support cache extension.

        Args:
            extension: Cache extension to append

        Returns:
            True if extension was successful
        """
        return False