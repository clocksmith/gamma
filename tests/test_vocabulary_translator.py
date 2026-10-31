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
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np

from src.engines.sampling_utils import TRANSLATION_LOGIT_FLOOR
from src.mind_meld.core.meld_engine import EngineTokenizerAdapter
from src.mind_meld.translators.vocabulary_translator import (
    AligningVocabularyTranslator,
    FallbackToUnkTranslator,
    SemanticMappingTranslator,
    SubwordDecompositionTranslator,
    VocabularyIntersectionTranslator,
    VocabularyTranslator,
)


class MockTokenizer:
    """Mock tokenizer for testing vocabulary translation."""

    def __init__(self, vocab: dict, name: str = "mock", special_ids: set = None):
        self._vocab = vocab
        self._reverse_vocab = {v: k for k, v in vocab.items()}
        self.name_or_path = name
        self._special_ids = set(special_ids or ())

    def get_vocab(self) -> dict:
        return self._vocab.copy()

    def decode(self, token_ids, skip_special_tokens=False) -> str:
        if isinstance(token_ids, int):
            token_ids = [token_ids]
        tokens = []
        for tid in token_ids:
            if skip_special_tokens and tid in self._special_ids:
                continue
            tokens.append(self._reverse_vocab.get(tid, "<unk>"))
        return "".join(tokens)

    def encode(self, text, add_special_tokens=False) -> list:
        if not text:
            return []
        if text in self._vocab:
            return [self._vocab[text]]
        ids = []
        for char in text:
            if char in self._vocab:
                ids.append(self._vocab[char])
        return ids


class TestVocabularyTranslatorBase(unittest.TestCase):
    """Tests for VocabularyTranslator base class utilities."""

    def setUp(self):
        class ConcreteTranslator(VocabularyTranslator):
            def translate_logits(self, source_logits, source_tokenizer=None, target_tokenizer=None):
                pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
                return self._validate_input_vector(source_logits, pair_spec, kind="logits")

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

    def test_same_vocab_size_requires_identical_mapping(self):
        """Equal-sized vocabularies with different token-to-ID mappings must not be treated as compatible."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a")
        tok_a_copy = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a_copy")
        tok_permuted = MockTokenizer({"b": 0, "c": 1, "a": 2}, "permuted")
        tok_disjoint = MockTokenizer({"x": 0, "y": 1, "z": 2}, "b")
        tok_c = MockTokenizer({"a": 0, "b": 1}, "c")

        self.assertTrue(self.translator._same_vocab_size(tok_a, tok_a_copy))
        self.assertFalse(self.translator._same_vocab_size(tok_a, tok_permuted))
        self.assertFalse(self.translator._same_vocab_size(tok_a, tok_disjoint))
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
        """Test that identical vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1, "c": 2}, "tok")
        logits = np.array([1.0, 2.0, 3.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_intersection_mask_applied(self):
        """Test that intersection maps common tokens to target IDs and floors non-common tokens."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2, "d": 3}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "x": 2, "y": 3, "z": 4}, "b")

        logits = np.array([1.0, 2.0, 3.0, 4.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (5,))
        self.assertEqual(result[0], 1.0)
        self.assertEqual(result[1], 2.0)
        self.assertEqual(result[2], TRANSLATION_LOGIT_FLOOR)
        self.assertEqual(result[3], TRANSLATION_LOGIT_FLOOR)
        self.assertEqual(result[4], TRANSLATION_LOGIT_FLOOR)

    def test_no_common_tokens_rejected(self):
        """Test that disjoint vocabularies raise ValueError instead of falling back."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"x": 0, "y": 1, "z": 2}, "b")

        logits = np.array([1.0, 2.0])
        with self.assertRaises(ValueError):
            self.translator.translate_logits(logits, tok_a, tok_b)

    def test_mask_cached(self):
        """Test that intersection map is cached."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "x": 1, "y": 2}, "b")

        logits = np.array([1.0, 2.0])
        self.translator.translate_logits(logits, tok_a, tok_b)

        cache_key = self.translator._make_cache_key(tok_a, tok_b, "intersection_map")
        self.assertIsNotNone(self.translator._get_cached(cache_key))


class TestAligningVocabularyTranslator(unittest.TestCase):
    """Tests for AligningVocabularyTranslator."""

    def setUp(self):
        self.translator = AligningVocabularyTranslator(verbose=False)

    def test_same_vocab_passthrough(self):
        """Test that identical vocabs pass through unchanged."""
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
        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], 3.0)
        self.assertEqual(result[2], TRANSLATION_LOGIT_FLOOR)

    def test_flatten_multidim_logits(self):
        """Test that multi-dimensional logits are flattened."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits_2d = np.array([[1.0, 2.0]])

        result = self.translator.translate_logits(logits_2d, tok, tok)
        self.assertEqual(result.ndim, 1)

    def test_rejects_low_mapping_without_fallback(self):
        """Test that inadequate mapping raises ValueError instead of copying raw indices."""
        tok_a = MockTokenizer({"": 0}, "a")
        tok_b = MockTokenizer({"x": 0, "y": 1}, "b")

        logits = np.array([1.0])
        with self.assertRaises(ValueError):
            self.translator.translate_logits(logits, tok_a, tok_b)

    def test_probability_translation(self):
        """Test translate_probabilities method."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        probs = np.array([0.6, 0.4])
        result = self.translator.translate_probabilities(probs, tok_a, tok_b)

        self.assertAlmostEqual(np.sum(result), 1.0, places=5)
        self.assertAlmostEqual(result[0], 0.6, places=5)
        self.assertAlmostEqual(result[1], 0.4, places=5)
        self.assertAlmostEqual(result[2], 0.0, places=5)


class TestSemanticMappingTranslator(unittest.TestCase):
    """Tests for SemanticMappingTranslator."""

    def setUp(self):
        self.translator = SemanticMappingTranslator(
            verbose=False,
            similarity_threshold=0.5
        )

    def test_same_vocab_passthrough(self):
        """Test that identical vocabs pass through unchanged."""
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

        self.assertEqual(result[0], 5.0)

    def test_semantic_similarity_fallback(self):
        """Test that similar tokens are mapped when no exact match."""
        tok_a = MockTokenizer({"aaa": 0, "bbb": 1}, "a")
        tok_b = MockTokenizer({"aaaa": 0, "bbbb": 1}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (2,))
        self.assertGreater(result[0], result[1])
        self.assertGreater(result[0], TRANSLATION_LOGIT_FLOOR)

    def test_get_token_embedding(self):
        """Test that token embeddings are generated."""
        embedding = self.translator._get_token_embedding("hello")
        self.assertEqual(embedding.shape, (256,))
        self.assertAlmostEqual(np.linalg.norm(embedding), 1.0, places=5)

    def test_similarity_threshold_respected(self):
        """Test that similarity threshold filters dissimilar tokens and rejects zero overlap."""
        translator = SemanticMappingTranslator(
            verbose=False,
            similarity_threshold=0.99
        )

        # Zero mapped tokens must raise ValueError, never fall back to raw index copy
        tok_zero_a = MockTokenizer({"xyz": 0}, "a")
        tok_zero_b = MockTokenizer({"abc": 0}, "b")
        with self.assertRaises(ValueError):
            translator.translate_logits(np.array([5.0]), tok_zero_a, tok_zero_b)

        # Partial overlap above minimum mapped threshold leaves unmapped target tokens at floor
        tok_a = MockTokenizer({"same": 0, "xyz": 1}, "a")
        tok_b = MockTokenizer({"same": 0, "abc": 1}, "b")
        result = translator.translate_logits(np.array([5.0, 3.0]), tok_a, tok_b)
        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], TRANSLATION_LOGIT_FLOOR)


class TestSubwordDecompositionTranslator(unittest.TestCase):
    """Tests for SubwordDecompositionTranslator."""

    def setUp(self):
        self.translator = SubwordDecompositionTranslator(verbose=False)

    def test_same_vocab_passthrough(self):
        """Test that identical vocabs pass through unchanged."""
        tok = MockTokenizer({"a": 0, "b": 1}, "tok")
        logits = np.array([1.0, 2.0])

        result = self.translator.translate_logits(logits, tok, tok)
        np.testing.assert_array_equal(result, logits)

    def test_subword_decomposition(self):
        """Test that tokens are decomposed into subwords."""
        tok_a = MockTokenizer({"ab": 0, "cd": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2, "d": 3}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (4,))
        self.assertGreater(result[0], TRANSLATION_LOGIT_FLOOR)

    def test_weighted_subwords(self):
        """Test that first subword gets higher weight."""
        tok_a = MockTokenizer({"abc": 0}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        logits = np.array([6.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result.shape, (3,))
        self.assertGreater(result[0], result[1])
        self.assertGreater(result[1], result[2])


class TestFallbackToUnkTranslator(unittest.TestCase):
    """Tests for FallbackToUnkTranslator."""

    def setUp(self):
        self.translator = FallbackToUnkTranslator(
            unk_token="<unk>",
            verbose=False
        )

    def test_same_vocab_passthrough(self):
        """Test that identical vocabs pass through unchanged."""
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
        """Test that unknown tokens map to UNK even when vocab sizes are equal."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "<unk>": 1}, "b")

        logits = np.array([5.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertEqual(result[0], 5.0)
        self.assertAlmostEqual(result[1], 3.0, places=5)

    def test_find_unk_token_variants(self):
        """Test that various UNK token formats are found."""
        tok = MockTokenizer({"a": 0, "[UNK]": 1}, "tok")
        translator = FallbackToUnkTranslator(verbose=False)
        unk_id = translator._find_unk_token_id(tok)
        self.assertEqual(unk_id, 1)

        tok2 = MockTokenizer({"a": 0, "<UNK>": 1}, "tok2")
        unk_id2 = translator._find_unk_token_id(tok2)
        self.assertEqual(unk_id2, 1)

    def test_unk_logit_aggregation(self):
        """Test that multiple unknown tokens aggregate to UNK."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a")
        tok_b = MockTokenizer({"a": 0, "<unk>": 1}, "b")

        logits = np.array([1.0, 2.0, 3.0])
        result = self.translator.translate_logits(logits, tok_a, tok_b)

        self.assertGreater(result[1], 2.0)


class TestTranslatorCaching(unittest.TestCase):
    """Tests for translator caching behavior."""

    def test_alignment_map_cached(self):
        """Test that alignment maps are cached."""
        translator = AligningVocabularyTranslator(use_cache=True, verbose=False)
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2}, "b")

        logits = np.array([1.0, 2.0])
        translator.translate_logits(logits, tok_a, tok_b)

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
        self.assertEqual(result.shape, (2,))


class TestStep1VocabularyTranslatorHardening(unittest.TestCase):
    """Tests for Step 1 vocabulary translator hardening requirements."""

    def test_vocab_mapping_inspected_once_at_construction_and_across_steps(self):
        """Token-to-ID mappings must be compared once when constructing or binding a pair, not per token."""
        tok_a = MockTokenizer({"alpha": 0, "beta": 1, "gamma": 2}, "a")
        tok_b = MockTokenizer({"beta": 0, "gamma": 1, "alpha": 2}, "b")
        tok_a.get_vocab = MagicMock(wraps=tok_a.get_vocab)
        tok_b.get_vocab = MagicMock(wraps=tok_b.get_vocab)

        translator = AligningVocabularyTranslator(
            source_tokenizer=tok_a,
            target_tokenizer=tok_b,
        )
        self.assertEqual(tok_a.get_vocab.call_count, 1)
        self.assertEqual(tok_b.get_vocab.call_count, 1)

        for step in range(5):
            logits = np.array([1.0 + step, 2.0 + step, 3.0 + step])
            out_logits = translator.translate_logits(logits)
            self.assertEqual(out_logits.shape, (3,))
            probs = np.array([0.2, 0.3, 0.5])
            out_probs = translator.translate_probabilities(probs)
            self.assertAlmostEqual(float(np.sum(out_probs)), 1.0, places=5)

        # Still only 1 get_vocab() call per tokenizer after 5 logit + 5 probability steps
        self.assertEqual(tok_a.get_vocab.call_count, 1)
        self.assertEqual(tok_b.get_vocab.call_count, 1)

    def test_engine_tokenizer_adapter_wrappers_reuse_memoized_pair_spec(self):
        """Fresh EngineTokenizerAdapter wrappers around the same engines must not re-run get_vocab()."""
        vocab_a = {"alpha": 0, "beta": 1, "gamma": 2}
        vocab_b = {"beta": 0, "gamma": 1, "alpha": 2}

        engine_a = MagicMock()
        engine_a.model_name = "engine_a"
        engine_a.get_vocab.return_value = vocab_a
        engine_a.encode.side_effect = lambda text, add_special_tokens=True: ([vocab_a[text]], None)
        engine_a.decode.side_effect = lambda ids, skip_special_tokens=False: {0: "alpha", 1: "beta", 2: "gamma"}[ids[0]]
        engine_a.tokenizer = SimpleNamespace(name_or_path="engine_a")

        engine_b = MagicMock()
        engine_b.model_name = "engine_b"
        engine_b.get_vocab.return_value = vocab_b
        engine_b.encode.side_effect = lambda text, add_special_tokens=True: ([vocab_b[text]], None)
        engine_b.decode.side_effect = lambda ids, skip_special_tokens=False: {0: "beta", 1: "gamma", 2: "alpha"}[ids[0]]
        engine_b.tokenizer = SimpleNamespace(name_or_path="engine_b")

        translator = AligningVocabularyTranslator()
        for _ in range(4):
            out = translator.translate_logits(
                np.array([10.0, 20.0, 30.0]),
                EngineTokenizerAdapter(engine_a),
                EngineTokenizerAdapter(engine_b),
            )
            np.testing.assert_allclose(out, np.array([20.0, 30.0, 10.0]))

        self.assertEqual(engine_a.get_vocab.call_count, 1)
        self.assertEqual(engine_b.get_vocab.call_count, 1)

    def test_equal_sized_permuted_vocabularies_translated_across_all_translators(self):
        """Equal-sized but permuted vocabularies must align by token identity, never passthrough by size."""
        tok_a = MockTokenizer({"alpha": 0, "beta": 1, "gamma": 2}, "a")
        tok_b = MockTokenizer({"beta": 0, "gamma": 1, "alpha": 2}, "b")
        logits = np.array([10.0, 20.0, 30.0])
        probs = np.array([0.1, 0.3, 0.6])

        translators = [
            VocabularyIntersectionTranslator(),
            AligningVocabularyTranslator(),
            SemanticMappingTranslator(similarity_threshold=0.5),
            SubwordDecompositionTranslator(),
            FallbackToUnkTranslator(),
        ]
        for translator in translators:
            with self.subTest(translator=type(translator).__name__):
                out_logits = translator.translate_logits(logits, tok_a, tok_b)
                np.testing.assert_allclose(out_logits, np.array([20.0, 30.0, 10.0]), rtol=1e-5, atol=1e-5)

                out_probs = translator.translate_probabilities(probs, tok_a, tok_b)
                np.testing.assert_allclose(out_probs, np.array([0.3, 0.6, 0.1]), rtol=1e-5, atol=1e-5)

    def test_identical_vocabularies_with_conflicting_special_semantics_rejected(self):
        """Equal get_vocab() mappings with mismatched special-token semantics must be rejected."""
        vocab = {"<s>": 0, "</s>": 1, "hello": 2}

        # Case 1: eos_token_id differs
        tok_a = MockTokenizer(vocab, "a")
        tok_a.bos_token = "<s>"
        tok_a.bos_token_id = 0
        tok_a.eos_token = "</s>"
        tok_a.eos_token_id = 1

        tok_b = MockTokenizer(vocab, "b")
        tok_b.bos_token = "</s>"
        tok_b.bos_token_id = 1
        tok_b.eos_token = "<s>"
        tok_b.eos_token_id = 0

        translator = AligningVocabularyTranslator()
        with self.assertRaises(ValueError):
            translator.translate_logits(np.array([1.0, 2.0, 3.0]), tok_a, tok_b)

        # Case 2: skip_special_tokens decode behavior differs despite matching attributes
        tok_c = MockTokenizer(vocab, "c", special_ids={0, 1})
        tok_c.bos_token = "<s>"
        tok_c.eos_token = "</s>"
        tok_d = MockTokenizer(vocab, "d", special_ids=set())
        tok_d.bos_token = "<s>"
        tok_d.eos_token = "</s>"

        with self.assertRaises(ValueError):
            AligningVocabularyTranslator().translate_logits(np.array([1.0, 2.0, 3.0]), tok_c, tok_d)

        # Case 3: chat_template differs on otherwise identical vocabularies
        tok_e = MockTokenizer(vocab, "e")
        tok_e.chat_template = "{{ messages }}"
        tok_f = MockTokenizer(vocab, "f")
        tok_f.chat_template = "<|user|>{{ messages }}"

        with self.assertRaises(ValueError):
            VocabularyIntersectionTranslator().translate_logits(np.array([1.0, 2.0, 3.0]), tok_e, tok_f)

    def test_logit_and_probability_dimension_mismatch_rejected(self):
        """Vectors whose length does not match source get_vocab() size must raise ValueError."""
        tok_a = MockTokenizer({"a": 0, "b": 1, "c": 2}, "a")
        tok_b = MockTokenizer({"a": 0, "b": 1, "c": 2, "d": 3}, "b")

        for translator in (
            VocabularyIntersectionTranslator(),
            AligningVocabularyTranslator(),
            SemanticMappingTranslator(),
            SubwordDecompositionTranslator(),
            FallbackToUnkTranslator(),
        ):
            with self.subTest(translator=type(translator).__name__):
                with self.assertRaises(ValueError):
                    translator.translate_logits(np.array([1.0, 2.0]), tok_a, tok_b)
                with self.assertRaises(ValueError):
                    translator.translate_probabilities(np.array([0.5, 0.5]), tok_a, tok_b)
                # Even on passthrough (tok_a -> tok_a), wrong vector length is rejected
                with self.assertRaises(ValueError):
                    translator.translate_logits(np.array([1.0, 2.0, 3.0, 4.0]), tok_a, tok_a)

    def test_inadequate_overlap_rejected_across_all_translators_without_raw_index_copy(self):
        """Inadequate overlap (< MIN_MAPPED_TOKENS on >=10-token vocabs) must raise ValueError across translators."""
        # 12-token vocabularies sharing only 2 tokens (< MIN_MAPPED_TOKENS=10)
        vocab_a = {f"src_{i}": i for i in range(10)}
        vocab_a["shared_0"] = 10
        vocab_a["shared_1"] = 11

        vocab_b = {f"tgt_{i}": i for i in range(10)}
        vocab_b["shared_0"] = 10
        vocab_b["shared_1"] = 11

        tok_a = MockTokenizer(vocab_a, "a")
        tok_b = MockTokenizer(vocab_b, "b")
        logits = np.arange(12, dtype=np.float32)

        for translator in (
            VocabularyIntersectionTranslator(),
            AligningVocabularyTranslator(),
            SemanticMappingTranslator(similarity_threshold=0.99),
            SubwordDecompositionTranslator(),
            FallbackToUnkTranslator(),
        ):
            with self.subTest(translator=type(translator).__name__):
                with self.assertRaises(ValueError):
                    translator.translate_logits(logits, tok_a, tok_b)
                with self.assertRaises(ValueError):
                    translator.translate_probabilities(np.full(12, 1.0 / 12.0), tok_a, tok_b)

    def test_fallback_to_unk_rejects_unmapped_tokens_when_target_has_no_unk(self):
        """FallbackToUnkTranslator must not silently map unknown tokens to token ID 0 when UNK is absent."""
        tok_a = MockTokenizer({"a": 0, "b": 1}, "a")
        tok_b = MockTokenizer({"a": 0, "c": 1}, "b")  # No <unk> token

        translator = FallbackToUnkTranslator()
        with self.assertRaises(ValueError):
            translator.translate_logits(np.array([5.0, 3.0]), tok_a, tok_b)

    def test_unsupported_tokenizer_introspection_rejected(self):
        """Missing or malformed tokenizer introspection must raise ValueError."""
        valid_tok = MockTokenizer({"a": 0, "b": 1}, "valid")
        logits = np.array([1.0, 2.0])

        # 1. None tokenizer
        with self.assertRaises(ValueError):
            AligningVocabularyTranslator().translate_logits(logits, None, valid_tok)

        # 2. Missing get_vocab()
        no_vocab_tok = SimpleNamespace(name_or_path="no_vocab")
        with self.assertRaises(ValueError):
            AligningVocabularyTranslator().translate_logits(logits, no_vocab_tok, valid_tok)

        # 3. get_vocab() returning non-dict
        bad_return_tok = SimpleNamespace(name_or_path="bad_ret", get_vocab=lambda: ["a", "b"])
        with self.assertRaises(ValueError):
            VocabularyIntersectionTranslator().translate_logits(logits, bad_return_tok, valid_tok)

        # 4. Non-contiguous token IDs (e.g. ID 5 in a 2-token vocab)
        non_contig_tok = MockTokenizer({"a": 0, "b": 5}, "non_contig")
        with self.assertRaises(ValueError):
            VocabularyIntersectionTranslator().translate_logits(logits, non_contig_tok, valid_tok)

        # 5. Negative token ID
        neg_id_tok = MockTokenizer({"a": -1, "b": 0}, "neg_id")
        with self.assertRaises(ValueError):
            VocabularyIntersectionTranslator().translate_logits(logits, neg_id_tok, valid_tok)

        # 6. Missing encode/decode on codec-requiring translator
        no_codec_tok = SimpleNamespace(name_or_path="no_codec", get_vocab=lambda: {"a": 0, "b": 1})
        with self.assertRaises(ValueError):
            AligningVocabularyTranslator().translate_logits(logits, no_codec_tok, valid_tok)


if __name__ == "__main__":
    unittest.main()
