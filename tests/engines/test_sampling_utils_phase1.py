"""
Tests for sampling_utils refactoring from Phase 1.

Tests the consolidated functions:
- get_top_k_tokens()
- process_logits_pipeline()
"""
import pytest
import numpy as np
from src.engines import sampling_utils


class TestGetTopKTokens:
    """Test get_top_k_tokens function."""

    def test_basic_functionality(self):
        """Test basic top-k token extraction."""
        # Create simple logits
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs, ids = sampling_utils.get_top_k_tokens(
            logits, k=3, token_text_fn=mock_token_text
        )

        assert len(tokens) == 3
        assert len(probs) == 3
        assert len(ids) == 3

        # Should return highest logits
        assert ids[0] == 4  # Highest logit
        assert ids[1] == 3  # Second highest
        assert ids[2] == 2  # Third highest

        # Probabilities should be in valid range
        assert all(0 <= p <= 1 for p in probs)
        # Note: top-k probs don't sum to 1.0 since they're from full distribution
        assert sum(probs) < 1.0  # Should be less than 1.0 since we filtered

    def test_with_probabilities(self):
        """Test with pre-computed probabilities."""
        probs = np.array([[0.1, 0.2, 0.3, 0.25, 0.15]])

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs_out, ids = sampling_utils.get_top_k_tokens(
            probs, k=3, token_text_fn=mock_token_text, is_probs=True
        )

        assert len(tokens) == 3
        # Should return tokens with highest probabilities
        assert ids[0] == 2  # 0.3
        assert ids[1] == 3  # 0.25
        assert ids[2] == 1  # 0.2

    def test_k_larger_than_vocab(self):
        """Test when k is larger than vocabulary."""
        logits = np.array([[1.0, 2.0, 3.0]])

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs, ids = sampling_utils.get_top_k_tokens(
            logits, k=10, token_text_fn=mock_token_text
        )

        # Should return all tokens
        assert len(tokens) == 3
        assert len(probs) == 3
        assert len(ids) == 3

    def test_k_zero(self):
        """Test with k=0 (should return all tokens)."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0]])

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs, ids = sampling_utils.get_top_k_tokens(
            logits, k=0, token_text_fn=mock_token_text
        )

        # Should return all tokens
        assert len(tokens) == 4

    def test_empty_logits(self):
        """Test with empty logits."""
        logits = np.array([[]])

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs, ids = sampling_utils.get_top_k_tokens(
            logits, k=3, token_text_fn=mock_token_text
        )

        # Should handle gracefully
        assert len(tokens) == 1
        assert tokens[0] == "<No Valid Tokens>"

    def test_all_inf_logits(self):
        """Test with all -inf logits."""
        logits = np.full((1, 5), -np.inf)

        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, probs, ids = sampling_utils.get_top_k_tokens(
            logits, k=3, token_text_fn=mock_token_text
        )

        # Should handle gracefully
        assert len(tokens) == 1
        assert tokens[0] == "<No Valid Tokens>"


class TestProcessLogitsPipeline:
    """Test process_logits_pipeline function."""

    def test_basic_pipeline(self):
        """Test basic logits processing pipeline."""
        # Create simple logits
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]])

        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=1.0, top_k=5, top_p=0.9
        )

        assert processed.shape == logits.shape
        assert not np.array_equal(processed, logits)  # Should be modified

    def test_temperature_scaling(self):
        """Test that temperature affects output."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

        # Low temperature should sharpen distribution
        processed_low = sampling_utils.process_logits_pipeline(
            logits.copy(), temperature=0.1, top_k=0, top_p=1.0
        )

        # High temperature should flatten distribution
        processed_high = sampling_utils.process_logits_pipeline(
            logits.copy(), temperature=2.0, top_k=0, top_p=1.0
        )

        # Verify they're different
        assert not np.array_equal(processed_low, processed_high)

    def test_top_k_filtering(self):
        """Test top-k filtering in pipeline."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]])

        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=1.0, top_k=3, top_p=1.0
        )

        # Most values should be -inf after top-k filtering
        num_inf = np.sum(np.isinf(processed))
        assert num_inf >= 7  # At least 7 tokens should be filtered out

    def test_top_p_filtering(self):
        """Test top-p (nucleus) filtering in pipeline."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]])

        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=1.0, top_k=0, top_p=0.5
        )

        # Some values should be -inf after top-p filtering
        num_inf = np.sum(np.isinf(processed))
        assert num_inf > 0  # At least some tokens should be filtered

    def test_return_intermediates(self):
        """Test returning intermediate values."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

        result = sampling_utils.process_logits_pipeline(
            logits, temperature=0.7, top_k=3, top_p=0.9,
            return_intermediates=True
        )

        assert isinstance(result, tuple)
        assert len(result) == 3

        logits_proc, logits_temp, logits_k = result

        # All should have same shape
        assert logits_proc.shape == logits_temp.shape == logits_k.shape == logits.shape

        # They should be different at each step
        assert not np.array_equal(logits_temp, logits)  # Temperature applied
        assert not np.array_equal(logits_k, logits_temp)  # Top-k applied
        assert not np.array_equal(logits_proc, logits_k)  # Top-p applied

    def test_no_filtering(self):
        """Test pipeline with no filtering (k=0, p=1.0)."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=1.0, top_k=0, top_p=1.0
        )

        # With no filtering and temp=1.0, should be unchanged
        assert np.array_equal(processed, logits)

    def test_combined_filtering(self):
        """Test combined top-k and top-p filtering."""
        logits = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]])

        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=1.0, top_k=5, top_p=0.8
        )

        # Both filters should be applied
        num_inf = np.sum(np.isinf(processed))
        # At least top-k should filter out 5 tokens
        assert num_inf >= 5


class TestSamplingUtilsIntegration:
    """Integration tests for sampling utils."""

    def test_full_sampling_workflow(self):
        """Test complete sampling workflow."""
        # Simulate model logits
        np.random.seed(42)
        logits = np.random.randn(1, 1000)

        # Process through pipeline
        processed = sampling_utils.process_logits_pipeline(
            logits, temperature=0.7, top_k=50, top_p=0.9
        )

        # Apply softmax
        probs = sampling_utils.softmax(processed)

        # Get top tokens
        def mock_token_text(token_id):
            return f"token_{token_id}"

        tokens, top_probs, ids = sampling_utils.get_top_k_tokens(
            processed, k=10, token_text_fn=mock_token_text
        )

        # Verify complete workflow
        assert len(tokens) == 10
        assert len(top_probs) == 10
        assert len(ids) == 10
        assert all(isinstance(t, str) for t in tokens)
        assert all(0 <= p <= 1 for p in top_probs)

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with same seed."""
        np.random.seed(42)
        logits1 = np.random.randn(1, 100)

        np.random.seed(42)
        logits2 = np.random.randn(1, 100)

        processed1 = sampling_utils.process_logits_pipeline(
            logits1, temperature=0.7, top_k=50, top_p=0.9
        )

        processed2 = sampling_utils.process_logits_pipeline(
            logits2, temperature=0.7, top_k=50, top_p=0.9
        )

        assert np.array_equal(processed1, processed2)
