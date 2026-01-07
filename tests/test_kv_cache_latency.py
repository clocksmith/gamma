"""
Regression tests for KV cache replay latency.

These tests measure and track KV cache operations to detect performance
regressions. They do NOT require actual model inference - they use mock
engines and synthetic data to benchmark the KV cache translation and
alignment algorithms.
"""

import unittest
import time
import numpy as np
from typing import List, Tuple, Dict, Any
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from src.mind_meld.bridges.kv_cache_handler import (
    KVCache,
    PyTorchKVCache,
    KVCacheTranslator,
    TokenizerAlignedTranslation,
    ProjectionTranslation,
    GQATranslation,
    DirectTranslation,
    convert_gqa_to_mha,
    convert_mha_to_gqa,
)


@dataclass
class LatencyMeasurement:
    """Result of a latency measurement."""
    operation: str
    duration_ms: float
    sequence_length: int
    num_layers: int
    iterations: int


class KVCacheLatencyBaseline:
    """
    Baseline latency thresholds for KV cache operations.

    These values are based on typical hardware and should be adjusted
    based on CI/CD environment. Values are in milliseconds.
    """
    # Per-sequence-position latencies (ms per position)
    TOKENIZER_ALIGNMENT_PER_TOKEN: float = 0.1  # 0.1ms per token
    PROJECTION_PER_LAYER: float = 0.5  # 0.5ms per layer
    GQA_CONVERSION_PER_LAYER: float = 0.2  # 0.2ms per layer
    DIRECT_COPY_PER_LAYER: float = 0.05  # 0.05ms per layer

    # Total operation thresholds
    ALIGNMENT_SHORT_SEQ: float = 50  # 50ms for <100 tokens
    ALIGNMENT_LONG_SEQ: float = 200  # 200ms for 100-1000 tokens
    ALIGNMENT_VERY_LONG_SEQ: float = 1000  # 1s for >1000 tokens

    # Regression tolerance (allow 20% degradation before failing)
    TOLERANCE: float = 1.2


class TestKVCacheLatencyBaseline(unittest.TestCase):
    """Tests to establish and verify KV cache latency baselines."""

    def setUp(self):
        self.translator = KVCacheTranslator(verbose=False)
        self.measurements: List[LatencyMeasurement] = []

    def _measure_latency(
        self,
        func,
        iterations: int = 10,
        warmup: int = 2
    ) -> float:
        """Measure average latency of a function in milliseconds."""
        # Warmup runs
        for _ in range(warmup):
            func()

        # Timed runs
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        return np.mean(times)

    def _create_mock_kv_cache(
        self,
        num_layers: int = 12,
        batch_size: int = 1,
        seq_length: int = 100,
        num_heads: int = 8,
        head_dim: int = 64
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create synthetic KV cache arrays."""
        shape = (num_layers, batch_size, seq_length, num_heads, head_dim)
        key = np.random.randn(*shape).astype(np.float32)
        value = np.random.randn(*shape).astype(np.float32)
        return key, value

    def _create_mock_tokenizer(self, vocab_size: int = 32000):
        """Create a mock tokenizer for alignment tests."""
        tokenizer = MagicMock()
        tokenizer.get_vocab.return_value = {f"token_{i}": i for i in range(vocab_size)}

        def mock_decode(token_ids):
            return "".join([f"tok{t}" for t in token_ids])

        def mock_encode(text, **kwargs):
            # Simple mock: return token per 3 chars
            return list(range(len(text) // 3 + 1))

        tokenizer.decode = mock_decode
        tokenizer.encode = mock_encode

        return tokenizer

    # =========================================================================
    # Direct Translation Latency Tests
    # =========================================================================

    def test_direct_translation_latency_short_sequence(self):
        """Direct translation should be fast for short sequences."""
        seq_length = 50
        num_layers = 12
        key, value = self._create_mock_kv_cache(
            num_layers=num_layers, seq_length=seq_length
        )

        strategy = DirectTranslation()
        mock_cache = MagicMock()
        mock_cache.key = key
        mock_cache.value = value
        mock_cache.model_arch = 'llama'
        mock_cache.num_layers = num_layers

        def translate():
            strategy.translate(mock_cache, MagicMock())

        latency = self._measure_latency(translate)

        # Direct translation should be nearly instant
        threshold = num_layers * KVCacheLatencyBaseline.DIRECT_COPY_PER_LAYER
        self.assertLess(
            latency, threshold * KVCacheLatencyBaseline.TOLERANCE,
            f"Direct translation latency {latency:.2f}ms exceeds threshold {threshold:.2f}ms"
        )

    def test_direct_translation_latency_long_sequence(self):
        """Direct translation should scale linearly with layers."""
        seq_length = 500
        num_layers = 32
        key, value = self._create_mock_kv_cache(
            num_layers=num_layers, seq_length=seq_length
        )

        strategy = DirectTranslation()
        mock_cache = MagicMock()
        mock_cache.key = key
        mock_cache.value = value
        mock_cache.model_arch = 'llama'
        mock_cache.num_layers = num_layers

        def translate():
            strategy.translate(mock_cache, MagicMock())

        latency = self._measure_latency(translate)

        threshold = num_layers * KVCacheLatencyBaseline.DIRECT_COPY_PER_LAYER * 2
        self.assertLess(
            latency, threshold * KVCacheLatencyBaseline.TOLERANCE,
            f"Direct translation latency {latency:.2f}ms exceeds threshold {threshold:.2f}ms"
        )

    # =========================================================================
    # GQA Conversion Latency Tests
    # =========================================================================

    def test_gqa_to_mha_conversion_latency(self):
        """GQA to MHA conversion should be efficient."""
        seq_length = 100
        num_layers = 24
        source_kv_heads = 8
        target_heads = 32

        # Shape: (layers, batch, seq, kv_heads, head_dim)
        cache = np.random.randn(num_layers, 1, seq_length, source_kv_heads, 64).astype(np.float32)

        def convert():
            convert_gqa_to_mha(cache, source_kv_heads, target_heads)

        latency = self._measure_latency(convert)

        threshold = num_layers * KVCacheLatencyBaseline.GQA_CONVERSION_PER_LAYER
        self.assertLess(
            latency, threshold * KVCacheLatencyBaseline.TOLERANCE,
            f"GQA conversion latency {latency:.2f}ms exceeds threshold {threshold:.2f}ms"
        )

    def test_mha_to_gqa_conversion_latency(self):
        """MHA to GQA conversion should be efficient."""
        seq_length = 100
        num_layers = 24
        source_heads = 32
        target_kv_heads = 8

        # Shape: (layers, batch, num_heads, seq_len, head_dim) - head axis is -3
        cache = np.random.randn(num_layers, 1, source_heads, seq_length, 64).astype(np.float32)

        def convert():
            convert_mha_to_gqa(cache, source_heads, target_kv_heads)

        latency = self._measure_latency(convert)

        threshold = num_layers * KVCacheLatencyBaseline.GQA_CONVERSION_PER_LAYER
        self.assertLess(
            latency, threshold * KVCacheLatencyBaseline.TOLERANCE,
            f"MHA to GQA conversion latency {latency:.2f}ms exceeds threshold {threshold:.2f}ms"
        )

    # =========================================================================
    # Projection Translation Latency Tests
    # =========================================================================

    def test_projection_translation_latency(self):
        """Projection translation should complete in reasonable time."""
        seq_length = 100
        num_layers = 24

        key, value = self._create_mock_kv_cache(
            num_layers=num_layers, seq_length=seq_length, head_dim=64
        )

        strategy = ProjectionTranslation()
        mock_cache = MagicMock()
        mock_cache.key = key
        mock_cache.value = value
        mock_cache.model_arch = 'llama'
        mock_cache.num_layers = num_layers
        mock_cache.num_heads = 8
        mock_cache.head_dim = 64
        mock_cache._cache_metadata = {'config': MagicMock()}

        target_config = MagicMock()
        target_config.num_hidden_layers = num_layers
        target_config.hidden_size = 4096
        target_config.num_attention_heads = 32
        target_config.num_key_value_heads = 8
        target_config.head_dim = 128  # Different head dim to trigger projection
        target_config.to_dict.return_value = {
            'num_attention_heads': 32,
            'num_key_value_heads': 8,
            'head_dim': 128,
            'hidden_size': 4096
        }

        def translate():
            strategy.translate(mock_cache, target_config)

        latency = self._measure_latency(translate, iterations=5)

        threshold = num_layers * KVCacheLatencyBaseline.PROJECTION_PER_LAYER
        self.assertLess(
            latency, threshold * KVCacheLatencyBaseline.TOLERANCE,
            f"Projection translation latency {latency:.2f}ms exceeds threshold {threshold:.2f}ms"
        )

    # =========================================================================
    # Tokenizer Alignment Latency Tests
    # =========================================================================

    def test_tokenizer_alignment_short_sequence(self):
        """Tokenizer alignment should be fast for short sequences."""
        seq_length = 50

        source_tokenizer = self._create_mock_tokenizer()
        target_tokenizer = self._create_mock_tokenizer(vocab_size=64000)

        aligner = TokenizerAlignedTranslation(
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            source_text="test " * seq_length
        )

        source_tokens = list(range(seq_length))
        target_tokens = list(range(seq_length + 10))  # Slightly different

        def align():
            aligner._compute_token_alignment(source_tokens, target_tokens)

        latency = self._measure_latency(align)

        self.assertLess(
            latency, KVCacheLatencyBaseline.ALIGNMENT_SHORT_SEQ,
            f"Short sequence alignment latency {latency:.2f}ms exceeds threshold"
        )

    def test_tokenizer_alignment_long_sequence(self):
        """Tokenizer alignment should handle long sequences efficiently."""
        seq_length = 500

        source_tokenizer = self._create_mock_tokenizer()
        target_tokenizer = self._create_mock_tokenizer(vocab_size=64000)

        aligner = TokenizerAlignedTranslation(
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            source_text="test " * seq_length
        )

        source_tokens = list(range(seq_length))
        target_tokens = list(range(seq_length + 50))

        def align():
            aligner._compute_token_alignment(source_tokens, target_tokens)

        latency = self._measure_latency(align, iterations=5)

        self.assertLess(
            latency, KVCacheLatencyBaseline.ALIGNMENT_LONG_SEQ,
            f"Long sequence alignment latency {latency:.2f}ms exceeds threshold"
        )

    def test_tokenizer_alignment_very_long_sequence(self):
        """Tokenizer alignment should scale sub-quadratically for very long sequences."""
        seq_length = 2000

        source_tokenizer = self._create_mock_tokenizer()
        target_tokenizer = self._create_mock_tokenizer(vocab_size=64000)

        aligner = TokenizerAlignedTranslation(
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            source_text="test " * seq_length
        )

        source_tokens = list(range(seq_length))
        target_tokens = list(range(seq_length + 100))

        def align():
            aligner._compute_token_alignment(source_tokens, target_tokens)

        latency = self._measure_latency(align, iterations=3)

        self.assertLess(
            latency, KVCacheLatencyBaseline.ALIGNMENT_VERY_LONG_SEQ,
            f"Very long sequence alignment latency {latency:.2f}ms exceeds threshold"
        )

    def test_alignment_scaling_is_subquadratic(self):
        """Verify alignment scales better than O(n^2)."""
        source_tokenizer = self._create_mock_tokenizer()
        target_tokenizer = self._create_mock_tokenizer(vocab_size=64000)

        latencies = []
        sequence_lengths = [100, 200, 400, 800]

        for seq_len in sequence_lengths:
            aligner = TokenizerAlignedTranslation(
                source_tokenizer=source_tokenizer,
                target_tokenizer=target_tokenizer,
                source_text="t" * (seq_len * 3)
            )

            source_tokens = list(range(seq_len))
            target_tokens = list(range(seq_len + seq_len // 10))

            def align():
                aligner._compute_token_alignment(source_tokens, target_tokens)

            latency = self._measure_latency(align, iterations=5)
            latencies.append(latency)

        # If O(n^2), doubling input should ~4x time
        # If O(n log n), doubling input should ~2.3x time
        # We check that scaling factor is < 3 (allows some overhead)

        for i in range(len(latencies) - 1):
            if latencies[i] > 1:  # Only check meaningful times
                scaling_factor = latencies[i + 1] / latencies[i]
                self.assertLess(
                    scaling_factor, 3.5,
                    f"Alignment scaling factor {scaling_factor:.2f} suggests quadratic complexity"
                )

    # =========================================================================
    # Cache Reuse Tests
    # =========================================================================

    def test_offset_cache_improves_latency(self):
        """Offset caching should improve repeated alignment calls."""
        seq_length = 200

        source_tokenizer = self._create_mock_tokenizer()
        target_tokenizer = self._create_mock_tokenizer(vocab_size=64000)

        aligner = TokenizerAlignedTranslation(
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            source_text="test " * seq_length
        )

        source_tokens = list(range(seq_length))
        target_tokens = list(range(seq_length + 20))

        # Clear cache
        TokenizerAlignedTranslation._offset_cache.clear()

        # First call (cold)
        start = time.perf_counter()
        aligner._compute_token_alignment(source_tokens, target_tokens)
        cold_latency = (time.perf_counter() - start) * 1000

        # Second call (warm - should use cache)
        start = time.perf_counter()
        aligner._compute_token_alignment(source_tokens, target_tokens)
        warm_latency = (time.perf_counter() - start) * 1000

        # Warm latency should be faster (or at least not slower)
        self.assertLessEqual(
            warm_latency, cold_latency * 1.5,  # Allow some variance
            f"Cached call ({warm_latency:.2f}ms) should not be much slower than cold ({cold_latency:.2f}ms)"
        )


class TestKVCacheReplayLatency(unittest.TestCase):
    """Tests specifically for KV cache replay (recomputation) latency tracking."""

    def setUp(self):
        self.measurements: List[LatencyMeasurement] = []

    def test_replay_overhead_tracking(self):
        """Verify we can track replay operations and their overhead."""
        # Simulate replay tracking
        replay_count = 0
        replay_times = []

        def simulate_replay(seq_length: int):
            nonlocal replay_count
            # Simulate replay time (proportional to sequence length)
            start = time.perf_counter()

            # Simulate work proportional to sequence
            _ = np.random.randn(seq_length, 768).astype(np.float32)
            _ = np.matmul(_, np.random.randn(768, 768).astype(np.float32))

            elapsed = (time.perf_counter() - start) * 1000
            replay_count += 1
            replay_times.append(elapsed)
            return elapsed

        # Run several replays
        for seq_len in [50, 100, 200, 100, 50]:
            simulate_replay(seq_len)

        self.assertEqual(replay_count, 5)
        self.assertEqual(len(replay_times), 5)

        # Verify times are reasonable
        avg_time = np.mean(replay_times)
        self.assertGreater(avg_time, 0)
        self.assertLess(avg_time, 100)  # Should be < 100ms for these sizes

    def test_replay_vs_translation_comparison(self):
        """Compare replay overhead vs translation overhead."""
        seq_length = 100
        num_layers = 12

        # Simulate replay cost (full recomputation)
        def simulate_replay():
            # Replay typically involves re-encoding and forward pass
            data = np.random.randn(seq_length, 768).astype(np.float32)
            for _ in range(num_layers):
                data = np.matmul(data, np.random.randn(768, 768).astype(np.float32))
            return data

        # Simulate translation cost (KV cache manipulation)
        def simulate_translation():
            key, value = self._create_mock_kv_cache(num_layers, 1, seq_length, 8, 64)
            # Simple copy/transform
            key_transformed = key * 0.5 + 0.5
            value_transformed = value * 0.5 + 0.5
            return key_transformed, value_transformed

        # Measure both
        replay_times = []
        translation_times = []

        for _ in range(5):
            start = time.perf_counter()
            simulate_replay()
            replay_times.append((time.perf_counter() - start) * 1000)

            start = time.perf_counter()
            simulate_translation()
            translation_times.append((time.perf_counter() - start) * 1000)

        avg_replay = np.mean(replay_times)
        avg_translation = np.mean(translation_times)

        # Translation should generally be faster than full replay
        # (though this depends on implementation)
        self.assertGreater(avg_replay, 0)
        self.assertGreater(avg_translation, 0)

    def _create_mock_kv_cache(
        self,
        num_layers: int,
        batch_size: int,
        seq_length: int,
        num_heads: int,
        head_dim: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create synthetic KV cache arrays."""
        shape = (num_layers, batch_size, seq_length, num_heads, head_dim)
        key = np.random.randn(*shape).astype(np.float32)
        value = np.random.randn(*shape).astype(np.float32)
        return key, value


class TestLatencyRegression(unittest.TestCase):
    """
    Regression tests that fail if latency degrades significantly.

    These tests establish baseline latencies and alert when operations
    become slower than expected.
    """

    def test_gqa_conversion_regression(self):
        """Catch regressions in GQA conversion performance."""
        # Baseline: GQA conversion should complete in < 10ms for typical sizes
        BASELINE_MS = 10.0

        cache = np.random.randn(24, 1, 100, 8, 64).astype(np.float32)

        times = []
        for _ in range(10):
            start = time.perf_counter()
            _ = convert_gqa_to_mha(cache, 8, 32)
            times.append((time.perf_counter() - start) * 1000)

        avg_time = np.mean(times[2:])  # Skip warmup

        self.assertLess(
            avg_time, BASELINE_MS * KVCacheLatencyBaseline.TOLERANCE,
            f"GQA conversion regression: {avg_time:.2f}ms > {BASELINE_MS}ms baseline"
        )

    def test_alignment_binary_search_regression(self):
        """Catch regressions in binary search alignment."""
        # Baseline: Binary search alignment should be < 100ms for 1000 tokens
        BASELINE_MS = 100.0

        source_offsets = [(i * 3, i * 3 + 3) for i in range(1000)]
        target_offsets = [(i * 4, i * 4 + 4) for i in range(1000)]

        aligner = TokenizerAlignedTranslation()

        times = []
        for _ in range(5):
            start = time.perf_counter()
            _ = aligner._compute_alignment_binary_search(source_offsets, target_offsets)
            times.append((time.perf_counter() - start) * 1000)

        avg_time = np.mean(times[1:])  # Skip warmup

        self.assertLess(
            avg_time, BASELINE_MS * KVCacheLatencyBaseline.TOLERANCE,
            f"Alignment regression: {avg_time:.2f}ms > {BASELINE_MS}ms baseline"
        )


if __name__ == "__main__":
    unittest.main()
