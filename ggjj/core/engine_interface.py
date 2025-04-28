# ggjj/core/engine_interface.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

class LLMEngine(ABC):
    """
    Abstract Base Class for Language Model Interaction Engines.

    Defines the interface for loading models, tokenizing text,
    predicting next tokens, and extracting internal states like
    probabilities and attention weights.

    Implementations should handle engine-specific data types (e.g.,
    torch.Tensor, tf.Tensor, jax.Array, mx.array, np.ndarray) internally
    but aim to provide standard Python types (lists, floats) for methods
    returning data directly to the UI/game logic layer where possible
    (e.g., get_probabilities_at_step, get_attention_for_visualization).
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        """
        Initializes the engine.

        Args:
            model_name: The identifier for the model (e.g., HF name, file path).
            engine_specific_config: Optional dictionary for engine-specific settings.
        """
        self.model_name = model_name
        self.engine_config = engine_specific_config or {}
        self.model = None
        self.tokenizer = None
        self._special_token_map = {} # Stores mapping from internal ID to game representation

    @abstractmethod
    def load(self):
        """
        Loads the model and tokenizer into memory.
        Must populate self.model, self.tokenizer, and self._special_token_map.
        """
        pass

    @abstractmethod
    def encode(self, text: str) -> Tuple[Any, Any]:
        """
        Encodes text into model-specific input IDs and attention masks.

        Args:
            text: The input string.

        Returns:
            A tuple containing (input_ids, attention_mask).
            The types will be engine-specific (e.g., Tensor, ndarray, list).
            Attention mask might be None for some engines (e.g., llama.cpp).
        """
        pass

    @abstractmethod
    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """
        Decodes token IDs (engine-specific format) back into a string.
        """
        pass

    @abstractmethod
    def predict_next(
        self,
        input_ids: Any, # Engine-specific type
        attention_mask: Any, # Engine-specific type or None
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """
        Performs a forward pass to predict the next token and returns relevant information.

        Input types for input_ids/attention_mask depend on the engine.

        Returns:
            A dictionary containing engine-specific tensors/arrays for logits/probabilities/states,
            but standard Python types for 'next_token_id', 'forward_time',
            'top_tokens_processed' (List[str]), and 'top_probs_processed' (List[float]).
            'attention' and 'hidden_states' may be engine-specific types or None.
        """
        pass

    @abstractmethod
    def get_vocabulary_size(self) -> int:
        """Returns the size of the model's vocabulary."""
        pass

    @abstractmethod
    def get_token_text(self, token_id: int) -> str:
        """
        Gets the text representation of a single token ID, handling special cases.
        Uses the _special_token_map for game-specific representations.
        """
        pass

    @abstractmethod
    def get_attention_for_visualization(
            self, attention_output: Any, input_ids: Any
        ) -> Optional[Tuple[List[str], List[float]]]:
        """
        Processes raw attention output into a format suitable for the UI.

        Args:
            attention_output: Raw attention data (engine-specific type or None).
            input_ids: Input token IDs (engine-specific type).

        Returns:
            Tuple (token_texts: List[str], normalized_scores: List[float]) or None.
            Implementations should return None if attention is unavailable or cannot be processed.
        """
        pass

    @abstractmethod
    def get_probabilities_at_step(
            self, logits_or_probs: Any, step_name: str, k: int
        ) -> Tuple[List[str], List[float], List[int]]:
        """
        Calculates and returns the top K tokens and probabilities from given logits or probabilities.

        Args:
            logits_or_probs: Engine-specific tensor/array of logits or probabilities.
            step_name: A descriptive name for the stage.
            k: The number of top tokens/probabilities to return.

        Returns:
            A tuple (top_token_texts: List[str], top_probabilities: List[float], top_token_ids: List[int]).
            Implementations MUST convert results to standard Python lists/floats/ints.
        """
        pass

    def get_special_token_representation(self, token_id: int) -> Optional[str]:
        """Returns the game-specific representation for a known special token ID."""
        return self._special_token_map.get(token_id)