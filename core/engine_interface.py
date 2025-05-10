from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

from . import config as cfg


class LLMEngine(ABC):
    """
    Abstract Base Class for Language Model Interaction Engines.
    Defines methods for model loading, tokenization, prediction,
    and extraction of internal states like probabilities and attention.
    Engines are responsible for managing their own KV cache for incremental decoding.
    """

    def __init__(
        self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.engine_config = engine_specific_config or {}
        self.model: Any = None
        self.tokenizer: Any = None
        self._special_token_id_to_game_repr: Dict[int, str] = {}
        self._token_cache: Dict[int, str] = {}  # Cache for get_token_text
        self._kv_cache: Any = None  # For storing and passing KV cache between steps

    @abstractmethod
    def load(self):
        """
        Loads the model and tokenizer.
        Initializes `self.model`, `self.tokenizer`, and `self._special_token_id_to_game_repr`.
        Should also initialize `self._kv_cache` to its initial state (e.g., None).
        """
        pass

    @abstractmethod
    def encode(
        self, text: str, add_special_tokens: bool = True
    ) -> Tuple[Any, Optional[Any]]:
        """
        Encodes text to input_ids and an optional attention_mask.
        `add_special_tokens` controls BOS/EOS.
        Returns engine-specific tensor/array types.
        """
        pass

    @abstractmethod
    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decodes token IDs (engine-specific) to a string."""
        pass

    @abstractmethod
    def predict_next(
        self,
        input_ids: Any,  # Should be the full sequence for first pass, or just new token(s) for incremental
        attention_mask: Optional[Any],
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        """
        Performs a forward pass to predict the next token and extract internal states.
        Manages and updates `self._kv_cache` internally if the engine uses it.
        If `input_ids` represents a full sequence (first step), `self._kv_cache` should be None or its initial state.
        If `input_ids` is just the new token for an incremental step, `self._kv_cache` from the previous step is used.

        Returns a dictionary containing:
        - 'next_token_id': The predicted next token ID (Python int).
        - 'logits_raw': Raw logits from the model (engine-specific tensor/array).
        - 'logits_processed': Logits after all sampling filters (engine-specific tensor/array).
        - 'probabilities_raw', 'probabilities_temp', 'probabilities_top_k', 'probabilities_processed':
          Corresponding probabilities (engine-specific tensor/array).
        - 'top_tokens_processed': List of top token strings after all filters (List[str]).
        - 'top_probs_processed': List of corresponding probabilities (List[float]).
        - 'attention': Attention weights if `output_attentions` is True (engine-specific, Optional).
        - 'hidden_states': Hidden states if `output_hidden_states` is True (engine-specific, Optional).
        - 'forward_time': Time taken for the forward pass (float).
        - `self._kv_cache` is updated internally by this method.
        """
        pass

    def reset_kv_cache(self):
        """Resets the internal KV cache to its initial state (e.g., None). Called when context changes non-incrementally."""
        self._kv_cache = None

    @abstractmethod
    def get_vocabulary_size(self) -> int:
        """Returns the model's vocabulary size."""
        pass

    @abstractmethod
    def get_token_text(self, token_id: int) -> str:
        """
        Gets the text representation for a given token ID.
        Uses an internal cache and the special token map.
        Subclasses must implement the actual decoding for unknown tokens.
        """
        if token_id in self._token_cache:
            return self._token_cache[token_id]
        game_repr = self._special_token_id_to_game_repr.get(token_id)
        if game_repr:
            self._token_cache[token_id] = game_repr
            return game_repr
        # Subclass must implement the rest for non-cached, non-special tokens
        raise NotImplementedError("Subclass must implement raw token-to-text decoding.")

    def is_word_like_token(
        self, token_id: int, token_text: Optional[str] = None
    ) -> bool:
        """
        Determines if a token is likely a 'word' based on heuristics.
        Engines can override for more precise, tokenizer-aware checks.
        """
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
        """
        Processes raw attention output (engine-specific) for UI visualization.
        `input_ids_for_viz` are the token IDs corresponding to the attention scores.
        Returns a tuple (list of token texts, list of normalized attention scores) or None if not available/supported.
        """
        pass

    @abstractmethod
    def get_probabilities_at_step(
        self, logits_or_probs: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """
        Extracts top K token texts, their probabilities, and their IDs from logits or probabilities.
        Input `logits_or_probs` is engine-specific. Output must be Python native types.
        """
        pass

    def get_config_summary(self) -> Dict[str, Any]:
        """Returns a dictionary of engine-specific configurations relevant for display after loading."""
        return {"engine_class": self.__class__.__name__}  # Basic default

    def _populate_special_token_map(self):
        """
        Helper for engines to map their tokenizer's special token IDs to GAMMA's game representations.
        This should be called by the engine's `load()` method after the tokenizer is initialized.
        """
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
                    # Handle tensor/array values by getting the item
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

        nl_attrs = [
            "newline_token_id",
            "nl_token_id",
            "line_break_token_id",
        ]  # Common attributes for newline
        for nl_attr in nl_attrs:
            newline_id_val = getattr(self.tokenizer, nl_attr, None)
            if newline_id_val is not None:
                try:
                    if hasattr(newline_id_val, "item") and callable(
                        newline_id_val.item
                    ):
                        newline_id_val = newline_id_val.item()
                    newline_id_int = int(newline_id_val)
                    self._special_token_id_to_game_repr[newline_id_int] = cfg.TOKEN_NL
                    break
                except (ValueError, TypeError, AttributeError) as e:
                    print(
                        f"{self.__class__.__name__} Warning: Could not convert/use newline token ID from '{nl_attr}': {newline_id_val} (Error: {e})"
                    )

        # Fallbacks for tokenizers with direct methods (e.g., LlamaCpp's internal one)
        # These should not overwrite existing mappings from _id attributes.
        if hasattr(self.tokenizer, "token_bos") and callable(self.tokenizer.token_bos):
            bos_id = self.tokenizer.token_bos()
            if (
                isinstance(bos_id, int)
                and bos_id not in self._special_token_id_to_game_repr
            ):
                self._special_token_id_to_game_repr[bos_id] = cfg.TOKEN_BOS
        if hasattr(self.tokenizer, "token_eos") and callable(self.tokenizer.token_eos):
            eos_id = self.tokenizer.token_eos()
            if (
                isinstance(eos_id, int)
                and eos_id not in self._special_token_id_to_game_repr
            ):
                self._special_token_id_to_game_repr[eos_id] = cfg.TOKEN_EOS
        if hasattr(self.tokenizer, "token_nl") and callable(self.tokenizer.token_nl):
            nl_id_direct = self.tokenizer.token_nl()
            if (
                isinstance(nl_id_direct, int)
                and nl_id_direct not in self._special_token_id_to_game_repr
            ):
                self._special_token_id_to_game_repr[nl_id_direct] = cfg.TOKEN_NL
