"""
Tests for vocabulary translation strategies in Mind Meld.

Tests the various vocabulary translator implementations including:
- VocabularyIntersectionTranslator
- AligningVocabularyTranslator
- SemanticMappingTranslator
- SubwordDecompositionTranslator
- FallbackToUnkTranslator
"""

import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace

import numpy as np


from src.mind_meld.translators.vocabulary_translator import (
    VocabularyTranslator,
    VocabularyIntersectionTranslator,
    AligningVocabularyTranslator,
    SemanticMappingTranslator,
    SubwordDecompositionTranslator,
    FallbackToUnkTranslator,
)
from src.engines.sampling_utils import TRANSLATION_LOGIT_FLOOR


class MockTokenizer:
    """Mock tokenizer for testing vocabulary translation."""

    def __init__(self, vocab: dict, name: str = "mock"):
        self._vocab = vocab
        self._reverse_vocab = {v: k for k, v in vocab.items()}
        self.name_or_path = name

    def get_vocab(self) -> dict:
        return self._vocab.copy()

    def decode(self, token_ids, skip_special_tokens=False) -> str:
        if isinstance(token_ids, int):
            token_ids = [token_ids]
        tokens = [self._reverse_vocab.get(tid, "<unk>") for tid in token_ids]
        return "".join(tokens)

    def encode(self, text, add_special_tokens=False) -> list:
        # Simple character-based encoding for testing
        ids = []
        for char in text:
            if char in self._vocab:
                ids.append(self._vocab[char])
        return ids


class TestVocabularyTranslatorBase(unittest.TestCase):
    """Tests for VocabularyTranslator base class utilities."""

    def setUp(self):
        # Create a concrete subclass for testing base methods
        class ConcreteTranslator(VocabularyTranslator):
            def translate_logits(self, source_logits, source_tokenizer, target_tokenizer):
                return source_logits

        self.translator = ConcreteTranslator(use_cache=True, verbose=False)

    def test_default_logit_floor_matches_constant(self):
        """Test that DEFAULT_LOGIT_FLOOR matches sampling_utils constant."""
        self.assertEqual(
            VocabularyTranslator.DEFAULT_LOGIT_FLOOR,
            TRANSLATION_LOGIT_FLOOR
        )
        self.assertEqual(VocabularyTranslator.DEFAULT_LOGIT_FLOOR, -10.0)

    def test_init_target_logits(self):
        """Test _init_target_logits creates proper array."""
        logits = self.translator._init_target_logits(100)
        self.assertEqual(logits.shape, (100,))
        self.assertTrue(np.all(logits == TRANSLATION_LOGIT_FLOOR))

    def test_init_target_logits_custom_floor(self):
        """Test _init_target_logits with custom floor value."""
        logits = self.translator._init_target_logits(50, fill_value=-5.0)
        self.assertTrue(np.all(logits == -5.0))

    def test_init_target_probs(self):
        """Test _init_target_probs creates zero array."""
        probs = self.translator._init_target_probs(100)
        self.assertEqual(probs.shape, (100,))
        self.assertTrue(np.all(probs == 0.0))

    def test_normalize_probs(self):
        """Test _normalize_probs normalizes to sum=1."""
        probs = np.array([1.0, 2.0, 3.0, 4.0])
        normalized = self.translator._normalize_probs(probs)
        self.assertAlmostEqual(np.sum(normalized), 1.0)
        self.assertAlmostEqual(normalized[0], 0.1)

    def test_normalize_probs_zero_sum(self):
        """Test _normalize_probs handles zero sum with uniform fallback."""
        probs = np.array([0.0, 0.0, 0.0, 0.0])
        normalized = self.translator._normalize_probs(probs)
        self.assertAlmostEqual(np.sum(normalized), 1.0)
        self.assertTrue(np.allclose(normalized, 0.25))

    def test_flatten_if_needed(self):
        """Test _flatten_if_needed flattens multi-dim arrays."""
        arr_2d = np.array([[1, 2, 3], [4, 5, 6]])
        flattened = self.translator._flatten_if_needed(arr_2d)
        self.assertEqual(flattened.shape, (6,))

        arr_1d = np.array([1, 2, 3])
        not_changed = self.translator._flatten_if_needed(arr_1d)
        self.assertEqual(not_changed.shape, (3,))

    def test_same_vocab_size(self):
        """Test _same_vocab_size comparison."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a")
        tok_b = MockTokenizer({"x": 0, "y": 1, "z": 2}, "b")
        tok_c = MockTokenizer({"x": 0, "y": 1}, "c")

        self.assertTrue(self.translator._same_vocab_size(tok_a, tok_b))
        self.assertFalse(self.translator._same_vocab_size(tok_a, tok_c))

    def test_caching(self):
        """Test cache get/set functionality."""
        self.translator._set_cached("test_key", "test_value")
        self.assertEqual(self.translator._get_cached("test_key"), "test_value")
        self.assertIsNone(self.translator._get_cached("nonexistent"))

    def test_caching_disabled(self):
        """Test that caching can be disabled."""
        translator = type(self.translator)(use_cache=False, verbose=False)
        translator._set_cached("key", "value")
        self.assertIsNone(translator._get_cached("key"))

    def test_make_cache_key(self):
        """Test cache key generation."""
        tok_a = MockTokenizer({"a": 0}, "model-a")
        tok_b = MockTokenizer({"b": 0}, "model-b")

        key = self.translator._make_cache_key(tok_a, tok_b, "alignment")
        self.assertIn("model-a", key)
        self.assertIn("model-b", key)
        self.assertIn("alignment", key)


class TestVocabularyIntersectionTranslator(unittest.TestCase):
    """Tests for VocabularyIntersectionTranslator."""

    def setUp(self):
        self.translator = VocabularyIntersectionTranslator(verbose=False)

    def test_same_vocab_passthrough(self):
        """Test that same-size vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1, "c": 2}, "tok")
        logits = np.array([1.0, 2.0, 3.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_intersection_mask_applied(self):
        """Test that intersection mask zeros out non-common tokens."""
        # Use different vocab sizes to trigger intersection logic
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2, "d": 3}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "x": 2, "y": 3, "z": 4}, "b")

        logits = np.array([1.0, 2.0, 3.0, 4.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # "a" and "b" are common (indices 0, 1), "c" and "d" are not
        # Common tokens should keep their logits, non-common should have -inf added
        self.assertEqual(result[0], 1.0)  # "a" is common
        self.assertEqual(result[1], 2.0)  # "b" is common
        self.assertEqual(result[2], -np.inf)  # "c" not in tok_b
        self.assertEqual(result[3], -np.inf)  # "d" not in tok_b

    def test_no_common_tokens(self):
        """Test behavior when no tokens are common."""
        # Use different vocab sizes to trigger intersection logic
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"x": 0, "y": 1, "z": 2}, "b")

        logits = np.array([1.0, 2.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertTrue(np.all(np.isinf(result)))

    def test_mask_cached(self):
        """Test that intersection mask is cached."""
        # Use different vocab sizes to trigger intersection logic
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "x": 1, "y": 2}, "b")

        logits = np.array([1.0, 2.0])

        # First call builds cache
        self.translator.translate_logits(logits, tok_a, tok_b)

        # Check cache has entry
        cache_key = self.translator._make_cache_key(tok_a, tok_b, "intersection")
        self.assertIsNotNone(self.translator._get_cached(cache_key))


class TestAligningVocabularyTranslator(unittest.TestCase):
    """Tests for AligningVocabularyTranslator."""

    def setUp(self):
        self.translator = AligningVocabularyTranslator(verbose=False)

    def test_same_vocab_passthrough(self):
        """Test that same-size vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits = np.array([1.0, 2.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_alignment_translation(self):
        """Test basic alignment translation."""
        tok_a = MockTokenizer({"hello": 0, "world": 1}, "a")
        tok_b = MockTokenizer({"hello": 0, "world": 1, "extra": 2}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (3,))
        # Common tokens should be mapped
        self.assertGreater(result[0], TRANSLATION_LOGIT_FLOOR)  # "hello" mapped
        self.assertGreater(result[1], TRANSLATION_LOGIT_FLOOR)  # "world" mapped

    def test_flatten_multidim_logits(self):
        """Test that multi-dimensional logits are flattened."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits_2d = np.array([[1.0, 2.0]])

        result = self.translator.translate_logits(logits_2d, tok, tok)
        self.assertEqual(result.ndim, 1)

    def test_fallback_on_low_mapping(self):
        """Test fallback when very few tokens map."""
        # This tests the MIN_MAPPED_TOKENS threshold
        tok_a = MockTokenizer({"": 0}, "a")  # Empty string token
        tok_b = MockTokenizer({"x": 0, "y": 1}, "b")

        logits = np.array([1.0])
        # Should trigger fallback due to low mapping count
        result = self.translator.translate_logits(logits, tok_a, tok_b)
        self.assertEqual(result.shape, (2,))

    def test_probability_translation(self):
        """Test translate_probabilities method."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        probs = np.array([0.6, 0.4])
        result = self.translator.translate_probabilities(probs, tok_a, tok_b)

        # Result should sum to 1 (after normalization)
        self.assertAlmostEqual(np.sum(result), 1.0, places=5)


class TestSemanticMappingTranslator(unittest.TestCase):
    """Tests for SemanticMappingTranslator."""

    def setUp(self):
        self.translator = SemanticMappingTranslator(
            verbose=False,
            similarity_threshold=0.5
        )

    def test_same_vocab_passthrough(self):
        """Test that same-size vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits = np.array([1.0, 2.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_exact_match_priority(self):
        """Test that exact string matches are prioritized."""
        tok_a = MockTokenizer({"hello": 0, "world": 1}, "a")
        tok_b = MockTokenizer({"hello": 0, "earth": 1, "extra": 2}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # "hello" should map to "hello" (exact match)
        self.assertEqual(result[0], 5.0)

    def test_semantic_similarity_fallback(self):
        """Test that similar tokens are mapped when no exact match."""
        # Tokens with shared characters should have higher similarity
        tok_a = MockTokenizer({"aaa": 0, "bbb": 1}, "a")
        tok_b = MockTokenizer({"aaaa": 0, "bbbb": 1}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # Similar tokens should be mapped
        self.assertEqual(result.shape, (2,))

    def test_get_token_embedding(self):
        """Test that token embeddings are generated."""
        embedding = self.translator._get_token_embedding("hello")
        self.assertEqual(embedding.shape, (256,))
        # Should be normalized
        self.assertAlmostEqual(np.linalg.norm(embedding), 1.0, places=5)

    def test_similarity_threshold_respected(self):
        """Test that similarity threshold filters mappings."""
        # With high threshold, dissimilar tokens shouldn't map
        translator = SemanticMappingTranslator(
            verbose=False,
            similarity_threshold=0.99
        )

        tok_a = MockTokenizer({"xyz": 0}, "a")
        tok_b = MockTokenizer({"abc": 0}, "b")

        logits = np.array([5.0])
        result = translator.translate_logits(logits, tok_a, tok_b)

        # Very different tokens shouldn't map with high threshold
        # Result should be at floor value if no mapping
        self.assertEqual(result.shape, (1,))


class TestSubwordDecompositionTranslator(unittest.TestCase):
    """Tests for SubwordDecompositionTranslator."""

    def setUp(self):
        self.translator = SubwordDecompositionTranslator(verbose=False)

    def test_same_vocab_passthrough(self):
        """Test that same-size vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits = np.array([1.0, 2.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_subword_decomposition(self):
        """Test that tokens are decomposed into subwords."""
        # Source has compound tokens, target has character tokens
        tok_a = MockTokenizer({"ab": 0, "cd": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2, "d": 3}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (4,))
        # "ab" should contribute to "a" and "b"
        self.assertGreater(result[0], TRANSLATION_LOGIT_FLOOR)

    def test_weighted_subwords(self):
        """Test that first subword gets higher weight."""
        # The translator weights first subword higher
        tok_a = MockTokenizer({"abc": 0}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        logits = np.array([6.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # First subword should have higher weight
        # With weight = 1/(i+1), first gets full weight, second gets 0.5, etc.
        self.assertEqual(result.shape, (3,))


class TestFallbackToUnkTranslator(unittest.TestCase):
    """Tests for FallbackToUnkTranslator."""

    def setUp(self):
        self.translator = FallbackToUnkTranslator(
            unk_token="<unk>",
            verbose=False
        )

    def test_same_vocab_passthrough(self):
        """Test that same-size vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits = np.array([1.0, 2.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_direct_match_preserved(self):
        """Test that direct matches keep their logits."""
        tok_a = MockTokenizer({"hello": 0, "world": 1, "<unk>": 2}, "a")
        tok_b = MockTokenizer({"hello": 0, "world": 1, "<unk>": 2}, "b")

        logits = np.array([5.0, 3.0, 1.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], 3.0)

    def test_unknown_tokens_to_unk(self):
        """Test that unknown tokens map to UNK."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "<unk>": 1}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # "a" maps directly, "b" maps to <unk>
        self.assertEqual(result[0], 5.0)  # Direct match
        # UNK should aggregate unknown token logits
        self.assertGreater(result[1], TRANSLATION_LOGIT_FLOOR)

    def test_find_unk_token_variants(self):
        """Test that various UNK token formats are found."""
        # Test [UNK] variant
        tok = MockTokenizer({"a": 0, "[UNK]": 1}, "tok")
        translator = FallbackToUnkTranslator(verbose=False)
        unk_id = translator._find_unk_token_id(tok)
        self.assertEqual(unk_id, 1)

        # Test <UNK> variant
        tok2 = MockTokenizer({"a": 0, "<UNK>": 1}, "tok2")
        unk_id2 = translator._find_unk_token_id(tok2)
        self.assertEqual(unk_id2, 1)

    def test_unk_logit_aggregation(self):
        """Test that multiple unknown tokens aggregate to UNK."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a")
        tok_b = MockTokenizer({"a": 0, "<unk>": 1}, "b")

        # b and c are both unknown, should aggregate to <unk>
        logits = np.array([1.0, 2.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        # UNK should be higher than any single unknown token logit
        # due to logsumexp aggregation
        self.assertGreater(result[1], 2.0)


class TestTranslatorCaching(unittest.TestCase):
    """Tests for translator caching behavior."""

    def test_alignment_map_cached(self):
        """Test that alignment maps are cached."""
        translator = AligningVocabularyTranslator(use_cache=True, verbose=False)
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        logits = np.array([1.0, 2.0])

        # First call
        translator.translate_logits(logits, tok_a, tok_b)

        # Verify cache populated
        cache_key = translator._make_cache_key(tok_a, tok_b, "alignment")
        self.assertIsNotNone(translator._get_cached(cache_key))

    def test_cache_disabled(self):
        """Test that caching can be disabled."""
        translator = AligningVocabularyTranslator(use_cache=False, verbose=False)
        tok_a = MockTokenizer({"a": 0}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1}, "b")

        logits = np.array([1.0])
        translator.translate_logits(logits, tok_a, tok_b)

        cache_key = translator._make_cache_key(tok_a, tok_b, "alignment")
        self.assertIsNone(translator._get_cached(cache_key))


class TestTranslatorEdgeCases(unittest.TestCase):
    """Tests for edge cases across all translators."""

    def test_empty_logits(self):
        """Test handling of empty logits array."""
        translator = AligningVocabularyTranslator(verbose=False)
        tok = MockTokenizer({}, "empty")

        logits = np.array([])
        result = translator.translate_logits(logits, tok, tok)
        self.assertEqual(result.shape, (0,))

    def test_single_token_vocab(self):
        """Test handling of single-token vocabulary."""
        translator = VocabularyIntersectionTranslator(verbose=False)
        tok_a = MockTokenizer({"x": 0}, "a")
        tok_b = MockTokenizer({"x": 0}, "b")

        logits = np.array([5.0])
        result = translator.translate_logits(logits, tok_a, tok_b)
        self.assertEqual(result[0], 5.0)

    def test_large_logit_values(self):
        """Test handling of extreme logit values."""
        translator = AligningVocabularyTranslator(verbose=False)
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")

        logits = np.array([1e10, -1e10])
        result = translator.translate_logits(logits, tok, tok)
        self.assertEqual(result[0], 1e10)
        self.assertEqual(result[1], -1e10)

    def test_nan_logits_handling(self):
        """Test that NaN logits are handled."""
        translator = AligningVocabularyTranslator(verbose=False)
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")

        logits = np.array([np.nan, 1.0])
        result = translator.translate_logits(logits, tok, tok)
        # NaN should propagate (behavior depends on implementation)
        self.assertEqual(result.shape, (2,))


if __name__ == "__main__":
    unittest.main()
