from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

from src.core import config as cfg


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
        return {"engine_class": self.__class__.__name__}

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