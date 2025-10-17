"""
Base test class for engine tests.

Provides common test patterns that all engines should satisfy.
"""
import pytest
import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseEngineTest(ABC):
    """Base class for engine tests."""

    @abstractmethod
    def create_engine(self, config: Dict[str, Any] = None):
        """Create an instance of the engine to test."""
        pass

    @abstractmethod
    def mock_model_loading(self, engine, mock_tokenizer, mock_model_output):
        """Mock model loading for the engine."""
        pass

    def test_engine_initialization(self, engine_config):
        """Test that engine can be initialized."""
        engine = self.create_engine(engine_config)
        assert engine is not None
        assert engine.model_name is not None
        assert engine.engine_config is not None

    def test_config_helpers(self, engine_config):
        """Test configuration helper methods."""
        engine = self.create_engine(engine_config)

        # Test default values
        assert isinstance(engine.get_trust_remote_code(), bool)
        assert isinstance(engine.get_verbose(), bool)
        assert isinstance(engine.get_max_tokens_for_display(), int)
        assert isinstance(engine.get_use_kv_cache(), bool)

        # Test that hf_token can be None
        assert engine.get_hf_token() is None or isinstance(engine.get_hf_token(), str)

    def test_encode_decode_cycle(self, mock_tokenizer, test_prompts):
        """Test that encode/decode cycle works."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, None)

        for prompt in test_prompts[:2]:  # Test first 2 prompts
            input_ids, attention_mask = engine.encode(prompt)
            assert input_ids is not None
            decoded = engine.decode(input_ids)
            assert isinstance(decoded, str)
            assert len(decoded) > 0

    def test_vocabulary_size(self, mock_tokenizer):
        """Test getting vocabulary size."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, None)

        vocab_size = engine.get_vocabulary_size()
        assert isinstance(vocab_size, int)
        assert vocab_size > 0

    def test_token_text_retrieval(self, mock_tokenizer):
        """Test get_token_text method."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, None)

        # Test regular token
        token_text = engine.get_token_text(100)
        assert isinstance(token_text, str)
        assert len(token_text) > 0

        # Test caching (second call should be cached)
        token_text_2 = engine.get_token_text(100)
        assert token_text == token_text_2

    def test_kv_cache_reset(self):
        """Test KV cache reset."""
        engine = self.create_engine()

        # Initially should be None
        assert engine._kv_cache is None

        # Set some mock cache
        engine._kv_cache = "mock_cache"
        assert engine._kv_cache == "mock_cache"

        # Reset should clear it
        engine.reset_kv_cache()
        assert engine._kv_cache is None

    def test_special_token_map(self, mock_tokenizer):
        """Test special token mapping."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, None)

        # Special tokens should be mapped
        assert hasattr(engine, "_special_token_id_to_game_repr")
        assert isinstance(engine._special_token_id_to_game_repr, dict)

    def test_prediction_output_structure(self, mock_tokenizer, mock_model_output, sampling_params):
        """Test that predict_next returns correct structure."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        # Encode a test prompt
        input_ids, attention_mask = engine.encode("Test prompt")

        # Predict next token
        output = engine.predict_next(
            input_ids,
            attention_mask,
            temperature=sampling_params["temperature"],
            top_k=sampling_params["top_k"],
            top_p=sampling_params["top_p"]
        )

        # Verify output structure
        from tests.engines.conftest import assert_valid_prediction_output
        assert_valid_prediction_output(output)

    def test_sampling_with_different_temperatures(self, mock_tokenizer, mock_model_output):
        """Test that different temperatures affect output."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        input_ids, attention_mask = engine.encode("Test")

        # Test with different temperatures
        for temp in [0.1, 0.7, 1.0, 1.5]:
            output = engine.predict_next(
                input_ids, attention_mask,
                temperature=temp, top_k=50, top_p=0.9
            )
            assert output["next_token_id"] >= 0
            assert "probabilities_processed" in output

    def test_top_k_filtering(self, mock_tokenizer, mock_model_output):
        """Test top-k filtering."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        input_ids, attention_mask = engine.encode("Test")

        # Test with different top-k values
        for k in [1, 10, 50]:
            output = engine.predict_next(
                input_ids, attention_mask,
                temperature=1.0, top_k=k, top_p=1.0
            )
            assert output["next_token_id"] >= 0
            # Top tokens should be <= k
            assert len(output["top_tokens_processed"]) <= k

    def test_top_p_filtering(self, mock_tokenizer, mock_model_output):
        """Test top-p (nucleus) filtering."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        input_ids, attention_mask = engine.encode("Test")

        # Test with different top-p values
        for p in [0.5, 0.9, 0.95]:
            output = engine.predict_next(
                input_ids, attention_mask,
                temperature=1.0, top_k=0, top_p=p
            )
            assert output["next_token_id"] >= 0

    def test_get_probabilities_at_step(self, mock_tokenizer, mock_model_output):
        """Test get_probabilities_at_step method."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        input_ids, attention_mask = engine.encode("Test")
        output = engine.predict_next(
            input_ids, attention_mask,
            temperature=0.7, top_k=50, top_p=0.9
        )

        # Get probabilities at different steps
        for step_name in ["raw", "temp", "processed"]:
            prob_key = f"probabilities_{step_name}"
            if prob_key in output:
                tokens, probs, ids = engine.get_probabilities_at_step(
                    output[prob_key], step_name, k=10
                )
                assert len(tokens) == len(probs) == len(ids)
                assert len(tokens) <= 10
                assert all(isinstance(t, str) for t in tokens)
                assert all(isinstance(p, (int, float)) for p in probs)

    def test_attention_visualization(self, mock_tokenizer, mock_model_output):
        """Test attention visualization method."""
        engine = self.create_engine()
        self.mock_model_loading(engine, mock_tokenizer, mock_model_output)

        input_ids, attention_mask = engine.encode("Test")

        # Most engines don't support attention, so None is acceptable
        result = engine.get_attention_for_visualization(None, input_ids)
        assert result is None or isinstance(result, tuple)

        if result is not None:
            tokens, scores = result
            assert len(tokens) == len(scores)
            assert all(isinstance(t, str) for t in tokens)
            assert all(isinstance(s, (int, float)) for s in scores)
