"""
Pytest fixtures for engine testing.

Provides mock objects and test utilities for testing LLM engines without
downloading actual models.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_tokenizer():
    """Mock HuggingFace tokenizer."""
    tokenizer = Mock()
    tokenizer.vocab_size = 32000
    tokenizer.eos_token_id = 2
    tokenizer.bos_token_id = 1
    tokenizer.pad_token_id = 0
    tokenizer.unk_token_id = 3
    tokenizer.unk_token = "<unk>"

    # Mock encode method
    def mock_encode(text: str, return_tensors=None, add_special_tokens=True):
        # Simple mock: return IDs based on text length
        ids = [1] + list(range(10, 10 + len(text.split()))) + ([2] if add_special_tokens else [])
        attention_mask = [1] * len(ids)

        if return_tensors == "pt":
            import torch
            return {
                "input_ids": torch.tensor([ids]),
                "attention_mask": torch.tensor([attention_mask])
            }
        elif return_tensors == "tf":
            import tensorflow as tf
            return {
                "input_ids": tf.constant([ids]),
                "attention_mask": tf.constant([attention_mask])
            }
        elif return_tensors == "np" or return_tensors == "jax":
            return {
                "input_ids": np.array([ids]),
                "attention_mask": np.array([attention_mask])
            }
        else:
            return {
                "input_ids": [ids],
                "attention_mask": [attention_mask]
            }

    tokenizer.__call__ = mock_encode

    # Mock decode method
    def mock_decode(ids: List[int], skip_special_tokens=False):
        # Simple mock: return text representation
        if skip_special_tokens:
            ids = [i for i in ids if i not in [0, 1, 2, 3]]
        return " ".join([f"token_{i}" for i in ids])

    tokenizer.decode = mock_decode

    # Mock convert_ids_to_tokens
    def mock_convert_ids_to_tokens(ids: List[int]):
        return [f"▁token_{i}" if i > 5 else f"<special_{i}>" for i in ids]

    tokenizer.convert_ids_to_tokens = mock_convert_ids_to_tokens

    return tokenizer


@pytest.fixture
def mock_model_output():
    """Mock model output with logits."""
    def _create_output(batch_size=1, seq_len=5, vocab_size=32000, framework="torch"):
        # Create random logits
        logits_np = np.random.randn(batch_size, seq_len, vocab_size).astype(np.float32)

        if framework == "torch":
            import torch
            output = Mock()
            output.logits = torch.from_numpy(logits_np)
            output.attentions = None
            output.hidden_states = None
            output.past_key_values = None
            return output
        elif framework == "tf":
            import tensorflow as tf
            output = Mock()
            output.logits = tf.constant(logits_np)
            output.attentions = None
            output.hidden_states = None
            output.past_key_values = None
            return output
        elif framework == "jax":
            import jax.numpy as jnp
            output = Mock()
            output.logits = jnp.array(logits_np)
            output.attentions = None
            output.hidden_states = None
            output.past_key_values = None
            return output
        elif framework == "numpy":
            return logits_np

        return logits_np

    return _create_output


@pytest.fixture
def test_prompts():
    """Common test prompts."""
    return [
        "Hello, how are you?",
        "What is the capital of France?",
        "Write a short poem about AI.",
        "Explain quantum computing in simple terms.",
        "The quick brown fox"
    ]


@pytest.fixture
def mock_model_config():
    """Mock model configuration."""
    return {
        "vocab_size": 32000,
        "hidden_size": 4096,
        "num_hidden_layers": 32,
        "num_attention_heads": 32,
        "intermediate_size": 11008,
        "max_position_embeddings": 2048,
        "model_type": "llama"
    }


@pytest.fixture
def engine_config():
    """Common engine configuration for tests."""
    return {
        "trust_remote_code": False,
        "verbose": False,
        "max_tokens_for_prob_display": 10,
        "use_kv_cache": True
    }


@pytest.fixture
def sampling_params():
    """Common sampling parameters."""
    return {
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.9
    }


def assert_valid_prediction_output(output: Dict[str, Any]):
    """Assert that prediction output has correct structure."""
    required_keys = [
        "next_token_id",
        "logits_raw",
        "logits_processed",
        "probabilities_raw",
        "probabilities_processed",
        "top_tokens_processed",
        "top_probs_processed",
        "forward_time"
    ]

    for key in required_keys:
        assert key in output, f"Missing key: {key}"

    assert isinstance(output["next_token_id"], int)
    assert isinstance(output["forward_time"], (int, float))
    assert isinstance(output["top_tokens_processed"], list)
    assert isinstance(output["top_probs_processed"], list)
    assert len(output["top_tokens_processed"]) == len(output["top_probs_processed"])


def assert_valid_tokenizer(tokenizer):
    """Assert that tokenizer has required attributes."""
    required_attrs = ["vocab_size", "decode", "eos_token_id"]
    for attr in required_attrs:
        assert hasattr(tokenizer, attr), f"Tokenizer missing attribute: {attr}"
