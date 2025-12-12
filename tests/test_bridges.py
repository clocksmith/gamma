"""Tests for Mind Meld bridges modules."""

import unittest
import numpy as np
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# State Bridge
from src.mind_meld.bridges.state_bridge import (
    BridgeState, StateBridge
)

# KV Cache Handler
from src.mind_meld.bridges.kv_cache_handler import (
    ModelArchitecture,
    ARCHITECTURE_GROUPS,
    get_architecture_group,
    architectures_compatible,
    get_model_architecture,
    get_attention_config,
)


# =============================================================================
# BridgeState Tests
# =============================================================================
class TestBridgeState(unittest.TestCase):
    """Tests for BridgeState dataclass."""

    def test_create_bridge_state(self):
        """Should create bridge state with all fields."""
        state = BridgeState(
            source_state={"key": "value"},
            target_state={"key": "value2"},
            translation_metadata={"mode": "direct"}
        )
        self.assertTrue(state.success)
        self.assertEqual(state.warnings, [])

    def test_post_init_warnings_default(self):
        """Should initialize warnings to empty list."""
        state = BridgeState(
            source_state={},
            target_state={},
            translation_metadata={}
        )
        self.assertEqual(state.warnings, [])
        self.assertIsInstance(state.warnings, list)

    def test_warnings_preserved_when_provided(self):
        """Should preserve provided warnings."""
        state = BridgeState(
            source_state={},
            target_state={},
            translation_metadata={},
            warnings=["Warning 1"]
        )
        self.assertEqual(state.warnings, ["Warning 1"])


# =============================================================================
# Architecture Groups Tests
# =============================================================================
class TestArchitectureGroups(unittest.TestCase):
    """Tests for architecture group functions."""

    def test_get_architecture_group_llama(self):
        """Should return all groups for llama."""
        groups = get_architecture_group('llama')
        self.assertIn('llama_family', groups)
        self.assertIn('mha_standard', groups)
        self.assertIn('gqa_models', groups)
        self.assertIn('rope_models', groups)

    def test_get_architecture_group_gpt2(self):
        """Should return correct groups for gpt2."""
        groups = get_architecture_group('gpt2')
        self.assertIn('gpt_family', groups)
        self.assertIn('mha_standard', groups)
        self.assertIn('absolute_pos', groups)

    def test_get_architecture_group_unknown(self):
        """Should return empty for unknown architecture."""
        groups = get_architecture_group('unknown')
        self.assertEqual(groups, [])

    def test_get_architecture_group_falcon(self):
        """Should return MQA group for falcon."""
        groups = get_architecture_group('falcon')
        self.assertIn('mqa_models', groups)
        self.assertIn('rope_models', groups)


# =============================================================================
# Architecture Compatibility Tests
# =============================================================================
class TestArchitecturesCompatible(unittest.TestCase):
    """Tests for architectures_compatible function."""

    def test_same_architecture_compatible(self):
        """Same architecture should always be compatible."""
        compatible, reason = architectures_compatible('llama', 'llama')
        self.assertTrue(compatible)
        self.assertEqual(reason, "same_architecture")

    def test_same_family_compatible(self):
        """Models in same family should be compatible."""
        compatible, reason = architectures_compatible('llama', 'mistral')
        self.assertTrue(compatible)
        self.assertIn('llama_family', reason)

    def test_gqa_to_mha_compatible(self):
        """GQA to MHA should be compatible."""
        # Gemma is GQA, gpt2 is MHA
        compatible, reason = architectures_compatible('gemma', 'gpt2')
        self.assertTrue(compatible)
        self.assertEqual(reason, "gqa_to_mha")

    def test_mqa_to_mha_compatible(self):
        """MQA to MHA should be compatible."""
        # Falcon is MQA, gpt2 is MHA
        compatible, reason = architectures_compatible('falcon', 'gpt2')
        self.assertTrue(compatible)
        self.assertEqual(reason, "mqa_to_mha")

    def test_incompatible_position_encodings(self):
        """Different position encodings should be incompatible."""
        # bloom uses ALiBi, llama uses RoPE
        compatible, reason = architectures_compatible('bloom', 'llama')
        self.assertFalse(compatible)
        self.assertIn("incompatible_position_encoding", reason)


# =============================================================================
# Model Architecture Detection Tests
# =============================================================================
class TestGetModelArchitecture(unittest.TestCase):
    """Tests for get_model_architecture function."""

    def test_none_config(self):
        """Should return unknown for None config."""
        result = get_model_architecture(None)
        self.assertEqual(result, 'unknown')

    def test_model_type_gemma(self):
        """Should detect gemma from model_type."""
        config = MagicMock()
        config.to_dict.return_value = {'model_type': 'gemma'}
        result = get_model_architecture(config)
        self.assertEqual(result, 'gemma')

    def test_model_type_llama(self):
        """Should detect llama from model_type."""
        config = MagicMock()
        config.to_dict.return_value = {'model_type': 'llama'}
        result = get_model_architecture(config)
        self.assertEqual(result, 'llama')

    def test_model_type_mistral(self):
        """Should detect mistral from model_type."""
        config = MagicMock()
        config.to_dict.return_value = {'model_type': 'mistral'}
        result = get_model_architecture(config)
        self.assertEqual(result, 'mistral')

    def test_architectures_list_fallback(self):
        """Should detect from architectures list when model_type empty."""
        config = MagicMock()
        config.to_dict.return_value = {
            'model_type': '',
            'architectures': ['LlamaForCausalLM']
        }
        result = get_model_architecture(config)
        self.assertEqual(result, 'llama')

    def test_sliding_window_detection(self):
        """Should use sliding_window for Gemma/Mistral heuristic."""
        config = MagicMock()
        config.to_dict.return_value = {
            'sliding_window': 4096,
            'num_attention_heads': 16,
            'num_key_value_heads': 8
        }
        result = get_model_architecture(config)
        self.assertEqual(result, 'mistral')  # GQA + sliding window

    def test_gqa_detection(self):
        """Should detect GQA models as llama."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 32,
            'num_key_value_heads': 8
        }
        result = get_model_architecture(config)
        self.assertEqual(result, 'llama')

    def test_mqa_detection(self):
        """Should detect MQA models as falcon."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 32,
            'num_key_value_heads': 1
        }
        result = get_model_architecture(config)
        self.assertEqual(result, 'falcon')

    def test_alibi_detection(self):
        """Should detect ALiBi models as bloom."""
        config = MagicMock()
        config.to_dict.return_value = {
            'alibi': True
        }
        result = get_model_architecture(config)
        self.assertEqual(result, 'bloom')

    def test_dict_fallback(self):
        """Should use __dict__ when to_dict not available."""
        @dataclass
        class SimpleConfig:
            model_type: str = 'qwen'

        config = SimpleConfig()
        # Remove to_dict if present
        result = get_model_architecture(config)
        self.assertEqual(result, 'qwen')


# =============================================================================
# Attention Config Tests
# =============================================================================
class TestGetAttentionConfig(unittest.TestCase):
    """Tests for get_attention_config function."""

    def test_standard_mha_config(self):
        """Should parse standard MHA config."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 12,
            'hidden_size': 768
        }
        result = get_attention_config(config)

        self.assertEqual(result['num_heads'], 12)
        self.assertEqual(result['num_kv_heads'], 12)
        self.assertEqual(result['head_dim'], 64)
        self.assertEqual(result['attention_type'], 'mha')

    def test_gqa_config(self):
        """Should detect GQA configuration."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 32,
            'num_key_value_heads': 8,
            'hidden_size': 4096
        }
        result = get_attention_config(config)

        self.assertEqual(result['num_heads'], 32)
        self.assertEqual(result['num_kv_heads'], 8)
        self.assertEqual(result['attention_type'], 'gqa')
        self.assertEqual(result['kv_groups'], 4)

    def test_mqa_config(self):
        """Should detect MQA configuration."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 32,
            'num_key_value_heads': 1,
            'hidden_size': 4096
        }
        result = get_attention_config(config)

        self.assertEqual(result['num_kv_heads'], 1)
        self.assertEqual(result['attention_type'], 'mqa')

    def test_explicit_head_dim(self):
        """Should use explicit head_dim when provided."""
        config = MagicMock()
        config.to_dict.return_value = {
            'num_attention_heads': 16,
            'head_dim': 128,
            'hidden_size': 2048
        }
        result = get_attention_config(config)

        self.assertEqual(result['head_dim'], 128)

    def test_gpt2_style_config(self):
        """Should handle GPT-2 style config keys."""
        config = MagicMock()
        config.to_dict.return_value = {
            'n_head': 12,
            'n_embd': 768
        }
        result = get_attention_config(config)

        self.assertEqual(result['num_heads'], 12)
        self.assertEqual(result['head_dim'], 64)


# =============================================================================
# StateBridge Tests
# =============================================================================
class TestStateBridge(unittest.TestCase):
    """Tests for StateBridge class."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_init_defaults(self):
        """Should initialize with default translators."""
        self.assertIsNotNone(self.bridge.kv_translator)
        self.assertIsNotNone(self.bridge.vocab_aligner)
        self.assertEqual(self.bridge.bridge_history, [])

    def test_create_projection_matrix_same_dim(self):
        """Should return identity for same dimensions."""
        matrix = self.bridge._create_projection_matrix(64, 64)
        np.testing.assert_array_almost_equal(matrix, np.eye(64))

    def test_create_projection_matrix_different_dims(self):
        """Should create proper projection matrix."""
        matrix = self.bridge._create_projection_matrix(64, 32)
        self.assertEqual(matrix.shape, (64, 32))

    def test_to_numpy_from_numpy(self):
        """Should return numpy array unchanged."""
        arr = np.array([1, 2, 3])
        result = self.bridge._to_numpy(arr)
        np.testing.assert_array_equal(result, arr)

    def test_to_numpy_from_list(self):
        """Should convert list to numpy."""
        lst = [1, 2, 3]
        result = self.bridge._to_numpy(lst)
        np.testing.assert_array_equal(result, np.array([1, 2, 3]))

    def test_from_numpy_to_numpy(self):
        """Should return numpy array when reference is numpy."""
        arr = np.array([1, 2, 3])
        ref = np.array([4, 5, 6])
        result = self.bridge._from_numpy(arr, ref)
        np.testing.assert_array_equal(result, arr)

    def test_get_tensor_dim(self):
        """Should return correct dimension."""
        tensor = np.zeros((10, 20, 30))
        self.assertEqual(self.bridge._get_tensor_dim(tensor, 0), 10)
        self.assertEqual(self.bridge._get_tensor_dim(tensor, 1), 20)
        self.assertEqual(self.bridge._get_tensor_dim(tensor, -1), 30)

    def test_infer_num_heads_from_shape(self):
        """Should infer heads from attention shape."""
        attention = np.zeros((2, 8, 16, 16))  # [batch, heads, seq, seq]
        result = self.bridge._infer_num_heads(attention)
        self.assertEqual(result, 8)

    def test_infer_num_heads_fallback(self):
        """Should return default for invalid shape."""
        attention = np.zeros((10,))  # 1D
        result = self.bridge._infer_num_heads(attention)
        self.assertEqual(result, 12)  # Default


# =============================================================================
# Tensor Projection Tests
# =============================================================================
class TestTensorProjection(unittest.TestCase):
    """Tests for tensor projection in StateBridge."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_project_tensor_basic(self):
        """Should project tensor to new dimension."""
        tensor = np.random.randn(10, 64)
        result = self.bridge._project_tensor(tensor, 64, 32)
        self.assertEqual(result.shape, (10, 32))

    def test_project_tensor_3d(self):
        """Should handle 3D tensors."""
        tensor = np.random.randn(2, 10, 64)
        result = self.bridge._project_tensor(tensor, 64, 128)
        self.assertEqual(result.shape, (2, 10, 128))

    def test_project_tensor_caching(self):
        """Should cache projection matrices."""
        tensor = np.random.randn(10, 64)
        cache_key = ('test', 64, 32)

        # First call - creates matrix
        self.bridge._project_tensor(tensor, 64, 32, cache_key=cache_key)
        self.assertIn(cache_key, self.bridge.projection_cache)

        # Second call - uses cached matrix
        cached = self.bridge.projection_cache[cache_key]
        self.bridge._project_tensor(tensor, 64, 32, cache_key=cache_key)
        self.assertIs(self.bridge.projection_cache[cache_key], cached)


# =============================================================================
# Attention Head Translation Tests
# =============================================================================
class TestAttentionHeadTranslation(unittest.TestCase):
    """Tests for attention head translation."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_merge_heads_perfect_division(self):
        """Should merge heads when evenly divisible."""
        # 8 heads -> 4 heads
        attention = np.random.randn(2, 8, 10, 10)
        result = self.bridge._translate_attention_heads(attention, 8, 4)
        self.assertEqual(result.shape[-3], 4)

    def test_merge_heads_imperfect_division(self):
        """Should truncate when not evenly divisible."""
        # 7 heads -> 4 heads
        attention = np.random.randn(2, 7, 10, 10)
        result = self.bridge._translate_attention_heads(attention, 7, 4)
        self.assertEqual(result.shape[-3], 4)

    def test_expand_heads(self):
        """Should duplicate heads when expanding."""
        # 4 heads -> 8 heads
        attention = np.random.randn(2, 4, 10, 10)
        result = self.bridge._translate_attention_heads(attention, 4, 8)
        self.assertEqual(result.shape[-3], 8)

    def test_expand_heads_with_remainder(self):
        """Should handle expansion with remainder."""
        # 3 heads -> 7 heads
        attention = np.random.randn(2, 3, 10, 10)
        result = self.bridge._translate_attention_heads(attention, 3, 7)
        self.assertEqual(result.shape[-3], 7)


# =============================================================================
# Mask Adjustment Tests
# =============================================================================
class TestMaskAdjustment(unittest.TestCase):
    """Tests for mask length adjustment."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_same_length(self):
        """Should return original mask when same length."""
        mask = np.ones((1, 10))
        reference = np.zeros((1, 10))
        result = self.bridge._adjust_mask_length(mask, reference)
        np.testing.assert_array_equal(result, mask)

    def test_truncate_mask(self):
        """Should truncate mask when longer."""
        mask = np.ones((1, 20))
        reference = np.zeros((1, 10))
        result = self.bridge._adjust_mask_length(mask, reference)
        result_np = self.bridge._to_numpy(result)
        self.assertEqual(result_np.shape[-1], 10)

    def test_pad_mask(self):
        """Should pad mask when shorter."""
        mask = np.ones((1, 5))
        reference = np.zeros((1, 10))
        result = self.bridge._adjust_mask_length(mask, reference)
        result_np = self.bridge._to_numpy(result)
        self.assertEqual(result_np.shape[-1], 10)
        # First 5 should be 1, rest should be 0
        np.testing.assert_array_equal(result_np[0, :5], np.ones(5))
        np.testing.assert_array_equal(result_np[0, 5:], np.zeros(5))


# =============================================================================
# Position ID Adjustment Tests
# =============================================================================
class TestPositionIdAdjustment(unittest.TestCase):
    """Tests for position ID adjustment."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_adjust_position_ids(self):
        """Should generate new position IDs for reference length."""
        position_ids = np.arange(5)
        reference = np.zeros(10)
        result = self.bridge._adjust_position_ids(position_ids, reference)
        result_np = self.bridge._to_numpy(result)
        np.testing.assert_array_equal(result_np, np.arange(10))


# =============================================================================
# Bridge States Integration Tests
# =============================================================================
class TestBridgeStatesIntegration(unittest.TestCase):
    """Integration tests for bridge_states method."""

    def setUp(self):
        self.bridge = StateBridge(verbose=False)

    def test_bridge_empty_source(self):
        """Should handle source with no components."""
        source = MagicMock()
        source.kv_cache = None
        source.last_hidden_states = None
        source.last_attention = None

        target = MagicMock()

        result = self.bridge.bridge_states(source, target)

        self.assertIsInstance(result, BridgeState)
        self.assertIn("Source has no KV cache to bridge", result.warnings)

    def test_records_to_history(self):
        """Should record bridge operations to history."""
        source = MagicMock()
        source.kv_cache = None
        target = MagicMock()

        initial_len = len(self.bridge.bridge_history)
        self.bridge.bridge_states(source, target)

        self.assertEqual(len(self.bridge.bridge_history), initial_len + 1)

    def test_custom_components(self):
        """Should only bridge specified components."""
        source = MagicMock()
        source.kv_cache = None
        source.last_hidden_states = None
        target = MagicMock()

        result = self.bridge.bridge_states(
            source, target,
            components=["hidden_states"]  # Only bridge hidden states
        )

        # Should not warn about KV cache since we didn't ask to bridge it
        kv_warnings = [w for w in result.warnings if "KV cache" in w]
        self.assertEqual(len(kv_warnings), 0)


if __name__ == "__main__":
    unittest.main()
