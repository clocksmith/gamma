"""
Test Engine Interface Abstract Base Class

Tests the LLMEngine abstract base class non-abstract methods including:
- TokenCategory enum
- KV cache management
- Special token handling
- Token categorization
- Token text retrieval and caching
- Configuration management
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from typing import Dict, Any, Tuple, Optional, List

from src.core.engine_interface import LLMEngine, TokenCategory
from src.core import config as cfg


class ConcreteEngine(LLMEngine):
    """Concrete implementation for testing."""

    def load(self):
        """Load the model."""
        self.model = MagicMock()
        self.tokenizer = MagicMock()

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[Any, Optional[Any]]:
        """Encode text to token IDs."""
        return ([1, 2, 3], None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode token IDs to text."""
        return "decoded text"

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
        """Predict next token."""
        return {"logits": np.array([0.1, 0.9])}

    def get_vocabulary_size(self) -> int:
        """Get vocabulary size."""
        return 32000

    def get_token_text(self, token_id: int) -> str:
        """Get token text."""
        # Try parent implementation first (handles cache and special tokens)
        try:
            return super().get_token_text(token_id)
        except NotImplementedError:
            # Parent couldn't handle it, provide our own implementation
            pass

        # Mock implementation for non-cached, non-special tokens
        token_map = {
            100: "hello",
            101: "world",
            102: " ",
            103: ".",
            104: "123",
            105: cfg.TOKEN_BOS,
            106: cfg.TOKEN_EOS,
            107: cfg.TOKEN_NL,
        }
        text = token_map.get(token_id, f"token_{token_id}")
        self._token_cache[token_id] = text
        return text

    def get_attention_for_visualization(
        self, attention_output: Any, input_ids_for_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        """Get attention for visualization."""
        return (["token1", "token2"], [0.3, 0.7])

    def get_probabilities_at_step(
        self, logits_or_probs: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """Get probabilities at step."""
        return (["token1", "token2"], [0.9, 0.1], [1, 2])

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert to numpy."""
        return np.array(tensor)

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert from numpy."""
        return array.tolist()

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate tensors."""
        return np.concatenate([tensor1, tensor2], axis=dim)

    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape."""
        if self._kv_cache is not None:
            return (2, 4, 8, 16)
        return None

    def get_num_layers(self) -> int:
        """Get number of layers."""
        return 12

    def get_vocab(self) -> Dict[str, int]:
        """Get vocabulary."""
        return {"hello": 100, "world": 101}

    def bridge_kv_cache_to(self, target_engine: 'LLMEngine') -> bool:
        """Bridge KV cache."""
        return True

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state."""
        if self._kv_cache is not None:
            return {"cache": "state"}
        return None

    def import_kv_cache_state(self, state: Dict[str, Any]) -> bool:
        """Import KV cache state."""
        self._kv_cache = state
        return True

    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append to input."""
        return list(input_ids) + [new_token_id]

    def get_device(self) -> str:
        """Get device."""
        return "cpu"


class TestTokenCategory(unittest.TestCase):
    """Test TokenCategory enum."""

    def test_enum_values(self):
        """Should have all expected categories."""
        self.assertEqual(TokenCategory.WORD.value, "word")
        self.assertEqual(TokenCategory.PUNCTUATION.value, "punctuation")
        self.assertEqual(TokenCategory.SPECIAL.value, "special")
        self.assertEqual(TokenCategory.WHITESPACE.value, "whitespace")
        self.assertEqual(TokenCategory.NUMBER.value, "number")
        self.assertEqual(TokenCategory.OTHER.value, "other")


class TestLLMEngineInit(unittest.TestCase):
    """Test LLMEngine initialization."""

    def test_initialization_default(self):
        """Should initialize with default values."""
        engine = ConcreteEngine(model_name="test-model")

        self.assertEqual(engine.model_name, "test-model")
        self.assertEqual(engine.engine_config, {})
        self.assertIsNone(engine.model)
        self.assertIsNone(engine.tokenizer)
        self.assertEqual(len(engine._special_token_id_to_game_repr), 0)
        self.assertEqual(len(engine._token_cache), 0)
        self.assertIsNone(engine._kv_cache)

    def test_initialization_with_config(self):
        """Should initialize with custom config."""
        config = {"param1": "value1", "param2": 42}
        engine = ConcreteEngine(model_name="test-model", engine_specific_config=config)

        self.assertEqual(engine.engine_config, config)


class TestKVCacheManagement(unittest.TestCase):
    """Test KV cache management methods."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_reset_kv_cache(self):
        """Should reset KV cache to None."""
        self.engine._kv_cache = "some_cache"

        self.engine.reset_kv_cache()

        self.assertIsNone(self.engine._kv_cache)

    def test_get_kv_cache_empty(self):
        """Should return None when cache is empty."""
        cache = self.engine.get_kv_cache()

        self.assertIsNone(cache)

    def test_get_kv_cache_with_data(self):
        """Should return cache when set."""
        self.engine._kv_cache = "test_cache"

        cache = self.engine.get_kv_cache()

        self.assertEqual(cache, "test_cache")

    def test_set_kv_cache_success(self):
        """Should set cache successfully."""
        self.engine.set_kv_cache("new_cache")

        self.assertEqual(self.engine._kv_cache, "new_cache")

    def test_set_kv_cache_with_dict(self):
        """Should set cache with dict data."""
        self.engine.set_kv_cache({"cache": "data"})

        self.assertEqual(self.engine._kv_cache, {"cache": "data"})

    def test_has_kv_cache_false(self):
        """Should return False when no cache."""
        self.assertFalse(self.engine.has_kv_cache())

    def test_has_kv_cache_true(self):
        """Should return True when cache exists."""
        self.engine._kv_cache = "cache_data"

        self.assertTrue(self.engine.has_kv_cache())


class TestTokenTextRetrieval(unittest.TestCase):
    """Test token text retrieval and caching."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_get_token_text_with_cache(self):
        """Should return cached token text."""
        self.engine._token_cache[100] = "cached_hello"

        text = self.engine.get_token_text(100)

        self.assertEqual(text, "cached_hello")

    def test_get_token_text_special_token(self):
        """Should return special token representation."""
        self.engine._special_token_id_to_game_repr[105] = cfg.TOKEN_BOS

        text = self.engine.get_token_text(105)

        self.assertEqual(text, cfg.TOKEN_BOS)
        # Should also be cached
        self.assertIn(105, self.engine._token_cache)

    def test_get_token_text_regular_token(self):
        """Should get token text and cache it."""
        text = self.engine.get_token_text(100)

        self.assertEqual(text, "hello")
        self.assertIn(100, self.engine._token_cache)

        # Second call should use cache
        text2 = self.engine.get_token_text(100)
        self.assertEqual(text2, "hello")


class TestIsWordLikeToken(unittest.TestCase):
    """Test is_word_like_token method."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_word_like_token_with_text(self):
        """Should identify word-like tokens when text provided."""
        # Setup token 100 to return "hello"
        self.engine._token_cache[100] = "hello"

        result = self.engine.is_word_like_token(100, "hello")

        self.assertTrue(result)

    def test_word_like_token_without_text(self):
        """Should identify word-like tokens when text not provided."""
        result = self.engine.is_word_like_token(100)  # Maps to "hello"

        self.assertTrue(result)

    def test_special_token_not_word_like(self):
        """Should return False for special tokens."""
        self.engine._special_token_id_to_game_repr[105] = cfg.TOKEN_BOS

        result = self.engine.is_word_like_token(105, cfg.TOKEN_BOS)

        self.assertFalse(result)

    def test_no_alpha_not_word_like(self):
        """Should return False for tokens with no letters."""
        result = self.engine.is_word_like_token(104, "123")

        self.assertFalse(result)

    def test_short_non_alpha_not_word_like(self):
        """Should return False for short non-alphabetic tokens."""
        result = self.engine.is_word_like_token(999, "1")

        self.assertFalse(result)

    def test_punctuation_not_word_like(self):
        """Should return False for punctuation."""
        result = self.engine.is_word_like_token(103, ".")

        self.assertFalse(result)


class TestConfigMethods(unittest.TestCase):
    """Test configuration methods."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_get_config_summary(self):
        """Should return config summary with engine class."""
        summary = self.engine.get_config_summary()

        self.assertIn("engine_class", summary)
        self.assertEqual(summary["engine_class"], "ConcreteEngine")

    def test_get_engine_specific_config_default(self):
        """Should return empty dict by default."""
        config = self.engine.get_engine_specific_config()

        self.assertEqual(config, {})


class TestPopulateSpecialTokenMap(unittest.TestCase):
    """Test _populate_special_token_map method."""

    def test_populate_without_tokenizer(self):
        """Should print warning when tokenizer not loaded."""
        engine = ConcreteEngine(model_name="test-model")

        with patch('sys.stdout') as mock_stdout:
            engine._populate_special_token_map()
            # Should not crash

    def test_populate_with_standard_tokens(self):
        """Should populate standard special tokens."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Setup special tokens
        engine.tokenizer.bos_token_id = 1
        engine.tokenizer.eos_token_id = 2
        engine.tokenizer.pad_token_id = 0
        engine.tokenizer.unk_token_id = 3

        engine._populate_special_token_map()

        self.assertIn(1, engine._special_token_id_to_game_repr)
        self.assertIn(2, engine._special_token_id_to_game_repr)

    def test_populate_with_tensor_token_ids(self):
        """Should handle tensor token IDs."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Mock tensor with item() method
        mock_tensor = MagicMock()
        mock_tensor.item.return_value = 5
        engine.tokenizer.bos_token_id = mock_tensor

        engine._populate_special_token_map()

        self.assertIn(5, engine._special_token_id_to_game_repr)

    def test_populate_with_numpy_token_ids(self):
        """Should handle numpy token IDs."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Create a custom class that only has numpy() method, not item()
        class NumpyTensor:
            def numpy(self):
                class NumpyArray:
                    def item(self):
                        return 7
                return NumpyArray()

        engine.tokenizer.eos_token_id = NumpyTensor()

        engine._populate_special_token_map()

        self.assertIn(7, engine._special_token_id_to_game_repr)

    def test_populate_with_newline_tokens(self):
        """Should handle newline token IDs."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Setup newline token
        engine.tokenizer.newline_token_id = 10

        engine._populate_special_token_map()

        self.assertEqual(
            engine._special_token_id_to_game_repr.get(10),
            cfg.TOKEN_NL
        )

    def test_populate_with_callable_tokens(self):
        """Should handle callable token methods."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Setup callable token methods
        engine.tokenizer.token_bos = MagicMock(return_value=11)
        engine.tokenizer.token_eos = MagicMock(return_value=12)
        engine.tokenizer.token_nl = MagicMock(return_value=13)

        engine._populate_special_token_map()

        self.assertEqual(engine._special_token_id_to_game_repr.get(11), cfg.TOKEN_BOS)
        self.assertEqual(engine._special_token_id_to_game_repr.get(12), cfg.TOKEN_EOS)
        self.assertEqual(engine._special_token_id_to_game_repr.get(13), cfg.TOKEN_NL)

    def test_populate_handles_conversion_errors(self):
        """Should handle token ID conversion errors gracefully."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Setup token that causes conversion error
        engine.tokenizer.bos_token_id = "invalid"

        with patch('sys.stdout'):
            engine._populate_special_token_map()
            # Should not crash

    def test_populate_handles_newline_conversion_errors(self):
        """Should handle newline token conversion errors gracefully."""
        engine = ConcreteEngine(model_name="test-model")
        engine.tokenizer = MagicMock()

        # Setup newline token that causes conversion error
        engine.tokenizer.newline_token_id = "invalid_newline"

        with patch('sys.stdout'):
            engine._populate_special_token_map()
            # Should not crash and should print warning


class TestSpecialTokenMethods(unittest.TestCase):
    """Test special token ID retrieval methods."""

    def setUp(self):
        """Create engine with mock tokenizer."""
        self.engine = ConcreteEngine(model_name="test-model")
        self.engine.tokenizer = MagicMock()

    def test_get_eos_token_id(self):
        """Should get EOS token ID."""
        self.engine.tokenizer.eos_token_id = 2

        eos_id = self.engine.get_eos_token_id()

        self.assertEqual(eos_id, 2)

    def test_get_eos_token_id_none(self):
        """Should return None when EOS token ID not available."""
        self.engine.tokenizer.eos_token_id = None

        eos_id = self.engine.get_eos_token_id()

        self.assertIsNone(eos_id)

    def test_get_eos_token_id_no_attribute(self):
        """Should return None when tokenizer has no eos_token_id."""
        delattr(self.engine.tokenizer, 'eos_token_id')

        eos_id = self.engine.get_eos_token_id()

        self.assertIsNone(eos_id)

    def test_get_unk_token_id(self):
        """Should get UNK token ID."""
        self.engine.tokenizer.unk_token_id = 3

        unk_id = self.engine.get_unk_token_id()

        self.assertEqual(unk_id, 3)

    def test_get_unk_token_id_none(self):
        """Should return None when UNK token ID not available."""
        self.engine.tokenizer.unk_token_id = None

        unk_id = self.engine.get_unk_token_id()

        self.assertIsNone(unk_id)

    def test_get_pad_token_id(self):
        """Should get PAD token ID."""
        self.engine.tokenizer.pad_token_id = 0

        pad_id = self.engine.get_pad_token_id()

        self.assertEqual(pad_id, 0)

    def test_get_pad_token_id_none(self):
        """Should return None when PAD token ID not available."""
        self.engine.tokenizer.pad_token_id = None

        pad_id = self.engine.get_pad_token_id()

        self.assertIsNone(pad_id)

    def test_get_bos_token_id(self):
        """Should get BOS token ID."""
        self.engine.tokenizer.bos_token_id = 1

        bos_id = self.engine.get_bos_token_id()

        self.assertEqual(bos_id, 1)

    def test_get_bos_token_id_none(self):
        """Should return None when BOS token ID not available."""
        self.engine.tokenizer.bos_token_id = None

        bos_id = self.engine.get_bos_token_id()

        self.assertIsNone(bos_id)

    def test_get_special_tokens(self):
        """Should get all special token IDs."""
        self.engine.tokenizer.eos_token_id = 2
        self.engine.tokenizer.unk_token_id = 3
        self.engine.tokenizer.pad_token_id = 0
        self.engine.tokenizer.bos_token_id = 1

        tokens = self.engine.get_special_tokens()

        self.assertEqual(tokens['eos'], 2)
        self.assertEqual(tokens['unk'], 3)
        self.assertEqual(tokens['pad'], 0)
        self.assertEqual(tokens['bos'], 1)


class TestIsSpecialToken(unittest.TestCase):
    """Test is_special_token method."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_is_special_token_true(self):
        """Should return True for special tokens."""
        self.engine._special_token_id_to_game_repr[105] = cfg.TOKEN_BOS

        result = self.engine.is_special_token(105)

        self.assertTrue(result)

    def test_is_special_token_false(self):
        """Should return False for regular tokens."""
        result = self.engine.is_special_token(100)

        self.assertFalse(result)


class TestGetTokenCategory(unittest.TestCase):
    """Test get_token_category method."""

    def setUp(self):
        """Create engine for testing."""
        self.engine = ConcreteEngine(model_name="test-model")

    def test_category_special(self):
        """Should categorize special tokens."""
        self.engine._special_token_id_to_game_repr[105] = cfg.TOKEN_BOS

        category = self.engine.get_token_category(105)

        self.assertEqual(category, TokenCategory.SPECIAL)

    def test_category_whitespace(self):
        """Should categorize whitespace tokens."""
        category = self.engine.get_token_category(102)  # Maps to " "

        self.assertEqual(category, TokenCategory.WHITESPACE)

    def test_category_punctuation(self):
        """Should categorize punctuation tokens."""
        category = self.engine.get_token_category(103)  # Maps to "."

        self.assertEqual(category, TokenCategory.PUNCTUATION)

    def test_category_number(self):
        """Should categorize number tokens."""
        category = self.engine.get_token_category(104)  # Maps to "123"

        self.assertEqual(category, TokenCategory.NUMBER)

    def test_category_word(self):
        """Should categorize word tokens."""
        category = self.engine.get_token_category(100)  # Maps to "hello"

        self.assertEqual(category, TokenCategory.WORD)

    def test_category_other(self):
        """Should categorize other tokens."""
        # Create a token that doesn't fit other categories
        self.engine._token_cache[999] = "§"

        category = self.engine.get_token_category(999)

        self.assertEqual(category, TokenCategory.OTHER)


def run_tests():
    """Run all engine interface tests."""
    print("=" * 80)
    print("Testing Engine Interface")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
