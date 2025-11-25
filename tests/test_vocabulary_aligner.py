"""Edge case tests for the Vocabulary Aligner.

Tests for vocabulary translation robustness including:
- Empty vocabularies
- Minimal overlap scenarios
- Special token handling
- Subword token detection
- Quality metric computation
- Cache invalidation
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict

import numpy as np

from src.mind_meld.translators.vocabulary_aligner import (
    VocabularyAligner,
    VocabularyMapping,
    MappingQuality,
)


class MockTokenizer:
    """Mock tokenizer for testing vocabulary extraction."""

    def __init__(self, vocab: Dict[str, int]):
        self._vocab = vocab

    def get_vocab(self) -> Dict[str, int]:
        return self._vocab


class MockTokenizerNoGetVocab:
    """Mock tokenizer without get_vocab method."""

    def __init__(self, vocab: Dict[str, int]):
        self.vocabulary = vocab


class MockTokenizerIterative:
    """Mock tokenizer that requires iterative vocab extraction."""

    def __init__(self, vocab: Dict[str, int]):
        self._vocab = vocab
        self._id_to_token = {v: k for k, v in vocab.items()}

    def get_vocab_size(self) -> int:
        return len(self._vocab)

    def token_to_id(self, token: str) -> int:
        return self._vocab.get(token, -1)

    def id_to_token(self, token_id: int) -> str:
        return self._id_to_token.get(token_id, "")


class TestVocabularyAlignerEdgeCases(unittest.TestCase):
    """Edge case tests for VocabularyAligner."""

    def setUp(self):
        self.aligner = VocabularyAligner(verbose=False, use_disk_cache=False)

    def test_empty_source_vocabulary(self):
        """Test handling of empty source vocabulary."""
        source = MockTokenizer({})
        target = MockTokenizer({"hello": 0, "world": 1})

        mapping = self.aligner.create_mapping(
            source, target, "empty_source", "target"
        )

        self.assertEqual(mapping.overlap_ratio, 0.0)
        self.assertEqual(len(mapping.common_tokens), 0)
        self.assertEqual(len(mapping.source_to_target), 0)

    def test_empty_target_vocabulary(self):
        """Test handling of empty target vocabulary."""
        source = MockTokenizer({"hello": 0, "world": 1})
        target = MockTokenizer({})

        mapping = self.aligner.create_mapping(
            source, target, "source", "empty_target"
        )

        self.assertEqual(mapping.overlap_ratio, 0.0)
        self.assertEqual(len(mapping.common_tokens), 0)
        self.assertEqual(len(mapping.target_to_source), 0)

    def test_both_empty_vocabularies(self):
        """Test handling of both empty vocabularies."""
        source = MockTokenizer({})
        target = MockTokenizer({})

        mapping = self.aligner.create_mapping(
            source, target, "empty1", "empty2"
        )

        self.assertEqual(mapping.overlap_ratio, 0.0)
        self.assertEqual(len(mapping.common_tokens), 0)

    def test_identical_vocabularies(self):
        """Test with identical vocabularies."""
        vocab = {"hello": 0, "world": 1, "test": 2}
        source = MockTokenizer(vocab.copy())
        target = MockTokenizer(vocab.copy())

        mapping = self.aligner.create_mapping(
            source, target, "source", "target"
        )

        self.assertEqual(mapping.overlap_ratio, 1.0)
        self.assertEqual(len(mapping.common_tokens), 3)
        # All source IDs should map to same target IDs
        for src_id, tgt_id in mapping.source_to_target.items():
            self.assertEqual(src_id, tgt_id)

    def test_no_overlap(self):
        """Test with completely disjoint vocabularies."""
        source = MockTokenizer({"cat": 0, "dog": 1})
        target = MockTokenizer({"red": 0, "blue": 1})

        mapping = self.aligner.create_mapping(
            source, target, "source", "target"
        )

        self.assertEqual(mapping.overlap_ratio, 0.0)
        self.assertEqual(len(mapping.common_tokens), 0)
        self.assertEqual(len(mapping.source_only), 2)
        self.assertEqual(len(mapping.target_only), 2)

    def test_partial_overlap(self):
        """Test with partial vocabulary overlap."""
        source = MockTokenizer({"hello": 0, "world": 1, "cat": 2})
        target = MockTokenizer({"hello": 0, "world": 1, "dog": 2})

        mapping = self.aligner.create_mapping(
            source, target, "source", "target"
        )

        # 2 common out of 4 unique = 0.5
        self.assertAlmostEqual(mapping.overlap_ratio, 0.5, places=2)
        self.assertEqual(len(mapping.common_tokens), 2)
        self.assertEqual(len(mapping.source_only), 1)
        self.assertEqual(len(mapping.target_only), 1)

    def test_different_token_ids(self):
        """Test mapping when same tokens have different IDs."""
        source = MockTokenizer({"hello": 0, "world": 1})
        target = MockTokenizer({"hello": 100, "world": 200})

        mapping = self.aligner.create_mapping(
            source, target, "source", "target"
        )

        self.assertEqual(mapping.overlap_ratio, 1.0)
        # Verify ID mapping is correct
        self.assertEqual(mapping.source_to_target[0], 100)
        self.assertEqual(mapping.source_to_target[1], 200)

    def test_special_token_detection(self):
        """Test detection of special tokens."""
        self.assertTrue(self.aligner._is_special_token("<s>"))
        self.assertTrue(self.aligner._is_special_token("</s>"))
        self.assertTrue(self.aligner._is_special_token("[CLS]"))
        self.assertTrue(self.aligner._is_special_token("[SEP]"))
        self.assertTrue(self.aligner._is_special_token("<|endoftext|>"))
        self.assertTrue(self.aligner._is_special_token("<pad>"))
        self.assertTrue(self.aligner._is_special_token("<unk>"))
        self.assertTrue(self.aligner._is_special_token("<mask>"))

        self.assertFalse(self.aligner._is_special_token("hello"))
        self.assertFalse(self.aligner._is_special_token("world"))
        self.assertFalse(self.aligner._is_special_token("the"))

    def test_subword_token_detection(self):
        """Test detection of subword tokens."""
        # BERT-style
        self.assertTrue(self.aligner._is_subword_token("##ing"))
        self.assertTrue(self.aligner._is_subword_token("##ed"))

        # SentencePiece-style
        self.assertTrue(self.aligner._is_subword_token("▁hello"))
        self.assertTrue(self.aligner._is_subword_token("Ġworld"))

        # BPE-style
        self.assertTrue(self.aligner._is_subword_token("@@tion"))

        # Not subwords
        self.assertFalse(self.aligner._is_subword_token("hello"))
        self.assertFalse(self.aligner._is_subword_token("world"))

    def test_quality_metrics_computation(self):
        """Test computation of quality metrics."""
        source_vocab = {"hello": 0, "world": 1, "<s>": 2, "▁the": 3}
        target_vocab = {"hello": 0, "world": 1, "<s>": 2, "cat": 3}
        common = {"hello", "world", "<s>"}

        quality = self.aligner._compute_quality_metrics(
            source_vocab, target_vocab, common
        )

        self.assertIsInstance(quality, MappingQuality)
        self.assertEqual(quality.common_token_count, 3)
        # 3 common out of 5 unique (hello, world, <s>, ▁the, cat)
        self.assertAlmostEqual(quality.overlap_ratio, 0.6, places=2)
        # Source coverage: 3/4 = 0.75
        self.assertAlmostEqual(quality.source_coverage, 0.75, places=2)
        # Target coverage: 3/4 = 0.75
        self.assertAlmostEqual(quality.target_coverage, 0.75, places=2)
        # Special token overlap: <s> is common, both have 1 special each
        self.assertEqual(quality.special_token_overlap, 1.0)

    def test_quality_level_classification(self):
        """Test quality level classification from score."""
        quality_excellent = MappingQuality(
            overlap_ratio=0.9,
            common_token_count=1000,
            source_coverage=0.9,
            target_coverage=0.9,
            special_token_overlap=1.0,
            subword_ratio=0.3
        )
        self.assertEqual(quality_excellent.quality_level, "excellent")

        quality_good = MappingQuality(
            overlap_ratio=0.7,
            common_token_count=500,
            source_coverage=0.7,
            target_coverage=0.7,
            special_token_overlap=0.8,
            subword_ratio=0.3
        )
        self.assertEqual(quality_good.quality_level, "good")

        quality_poor = MappingQuality(
            overlap_ratio=0.2,
            common_token_count=100,
            source_coverage=0.2,
            target_coverage=0.2,
            special_token_overlap=0.3,
            subword_ratio=0.1
        )
        self.assertEqual(quality_poor.quality_level, "poor")

    def test_fallback_vocabulary_extraction(self):
        """Test fallback methods for vocabulary extraction."""
        # Test vocabulary property
        tokenizer = MockTokenizerNoGetVocab({"hello": 0, "world": 1})
        vocab = self.aligner._extract_vocabulary(tokenizer)
        self.assertEqual(vocab, {"hello": 0, "world": 1})

    def test_iterative_vocabulary_extraction(self):
        """Test iterative vocabulary extraction."""
        tokenizer = MockTokenizerIterative({"hello": 0, "world": 1, "test": 2})
        vocab = self.aligner._extract_vocabulary(tokenizer)
        self.assertEqual(len(vocab), 3)

    def test_in_memory_cache(self):
        """Test that in-memory caching works."""
        source = MockTokenizer({"hello": 0})
        target = MockTokenizer({"hello": 0})

        # First call creates mapping
        mapping1 = self.aligner.create_mapping(
            source, target, "cache_test_source", "cache_test_target"
        )

        # Second call should return cached mapping
        mapping2 = self.aligner.create_mapping(
            source, target, "cache_test_source", "cache_test_target"
        )

        # Should be the exact same object
        self.assertIs(mapping1, mapping2)


class TestVocabularyMappingSerialization(unittest.TestCase):
    """Test serialization/deserialization of VocabularyMapping."""

    def test_mapping_to_dict(self):
        """Test mapping serialization to dictionary."""
        mapping = VocabularyMapping(
            source_to_target={0: 10, 1: 11},
            target_to_source={10: 0, 11: 1},
            common_tokens={0, 1},
            source_only={2},
            target_only={12},
            overlap_ratio=0.5,
            quality=None
        )

        data = mapping.to_dict()

        self.assertIn('source_to_target', data)
        self.assertIn('target_to_source', data)
        self.assertIn('overlap_ratio', data)
        # Keys should be strings for JSON compatibility
        self.assertIn('0', data['source_to_target'])

    def test_mapping_from_dict(self):
        """Test mapping deserialization from dictionary."""
        data = {
            'source_to_target': {'0': 10, '1': 11},
            'target_to_source': {'10': 0, '11': 1},
            'common_tokens': [0, 1],
            'source_only': [2],
            'target_only': [12],
            'overlap_ratio': 0.5
        }

        mapping = VocabularyMapping.from_dict(data)

        self.assertEqual(mapping.source_to_target[0], 10)
        self.assertEqual(mapping.target_to_source[10], 0)
        self.assertEqual(mapping.overlap_ratio, 0.5)
        self.assertIn(0, mapping.common_tokens)

    def test_mapping_roundtrip_with_quality(self):
        """Test roundtrip with quality metrics."""
        quality = MappingQuality(
            overlap_ratio=0.8,
            common_token_count=100,
            source_coverage=0.9,
            target_coverage=0.85,
            special_token_overlap=1.0,
            subword_ratio=0.3
        )
        mapping = VocabularyMapping(
            source_to_target={0: 0},
            target_to_source={0: 0},
            common_tokens={0},
            source_only=set(),
            target_only=set(),
            overlap_ratio=0.8,
            quality=quality
        )

        data = mapping.to_dict()
        restored = VocabularyMapping.from_dict(data)

        self.assertIsNotNone(restored.quality)
        self.assertEqual(restored.quality.common_token_count, 100)
        self.assertAlmostEqual(restored.quality.source_coverage, 0.9)


class TestLogitTranslation(unittest.TestCase):
    """Test logit translation between vocabularies."""

    def setUp(self):
        self.aligner = VocabularyAligner(verbose=False, use_disk_cache=False)

    def test_translate_logits_intersection(self):
        """Test intersection-based logit translation."""
        mapping = VocabularyMapping(
            source_to_target={0: 0, 1: 1},
            target_to_source={0: 0, 1: 1},
            common_tokens={0, 1},
            source_only={2},
            target_only=set(),
            overlap_ratio=0.67
        )

        source_logits = np.array([2.0, 1.0, 0.5])  # 3 tokens

        translated = self.aligner.translate_logits(
            source_logits,
            mapping,
            strategy="intersection"
        )

        # Translated should only have values for common tokens
        self.assertEqual(len(translated), 2)

    def test_translate_logits_with_temperature(self):
        """Test logit translation with temperature scaling."""
        mapping = VocabularyMapping(
            source_to_target={0: 0, 1: 1},
            target_to_source={0: 0, 1: 1},
            common_tokens={0, 1},
            source_only=set(),
            target_only=set(),
            overlap_ratio=1.0
        )

        source_logits = np.array([2.0, 1.0])

        # With temperature=1.0
        translated_t1 = self.aligner.translate_logits(
            source_logits, mapping, temperature=1.0
        )

        # With temperature=2.0 (more uniform)
        translated_t2 = self.aligner.translate_logits(
            source_logits, mapping, temperature=2.0
        )

        # Higher temperature should make distribution more uniform
        probs_t1 = np.exp(translated_t1) / np.sum(np.exp(translated_t1))
        probs_t2 = np.exp(translated_t2) / np.sum(np.exp(translated_t2))

        # Variance should be lower with higher temperature
        self.assertGreater(np.var(probs_t1), np.var(probs_t2))


if __name__ == "__main__":
    unittest.main()
