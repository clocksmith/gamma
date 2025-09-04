from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any, Union
from enum import Enum
import numpy as np

from src.core import config as cfg


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

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def encode(
        self, text: str, add_special_tokens: bool = True
    ) -> Tuple[Any, Optional[Any]]:
        pass

    @abstractmethod
    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        pass

    @abstractmethod
    def predict_next(
        self,
        input_ids: Any,
        attention_mask: Optional[Any],
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        pass

    def reset_kv_cache(self):
        self._kv_cache = None
    
    def get_kv_cache(self) -> Optional[Any]:
        """Get the current KV cache."""
        return self._kv_cache
    
    def set_kv_cache(self, cache: Any) -> bool:
        """Set the KV cache. Returns True if successful."""
        try:
            self._kv_cache = cache
            return True
        except Exception:
            return False

    @abstractmethod
    def get_vocabulary_size(self) -> int:
        pass

    @abstractmethod
    def get_token_text(self, token_id: int) -> str:
        if token_id in self._token_cache:
            return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr:
            self._token_cache[token_id] = game_repr
            return game_repr
        raise NotImplementedError("Subclass must implement raw token-to-text decoding.")

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
            print(
                f"{self.__class__.__name__} Warning: Tokenizer not loaded, cannot populate special token map."
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
                    print(
                        f"{self.__class__.__name__} Warning: Could not convert/use token ID for '{game_key}': {token_id_val} (Error: {e})"
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
                    print(
                        f"{self.__class__.__name__} Warning: Could not convert/use newline token ID from '{nl_attr}': {newline_id_val} (Error: {e})"
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

    @abstractmethod
    def bridge_kv_cache_to(self, target_engine: 'LLMEngine') -> bool:
        """Attempt to bridge KV cache to another engine."""
        pass
    
    @abstractmethod
    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging."""
        pass
    
    @abstractmethod
    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """Import KV cache state from another engine."""
        pass
    
    @abstractmethod
    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids tensor."""
        pass
    
    @abstractmethod
    def get_device(self) -> str:
        """Get device type (cpu, cuda, mps, etc)."""
        pass