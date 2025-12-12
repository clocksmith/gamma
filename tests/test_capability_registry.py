"""
Tests for Engine Capability Registry and helper constants.

Tests the capability registry functions and validates that engine
capabilities are properly defined. Also tests new helper constants.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from src.engines.capability_registry import (
    ENGINES,
    EngineCapabilities,
    EngineInfo,
    get_engine_info,
    list_engines,
    list_engines_with,
    check_compatibility,
    get_mind_meld_compatible_engines,
    get_engine_requirements,
    format_engine_table,
)
from src.engines.sampling_utils import (
    TRANSLATION_LOGIT_FLOOR,
    LOGIT_FLOOR,
    LOGIT_CEILING,
    EPSILON,
)
from src.mind_meld.core.meld_engine import (
    FALLBACK_TOP_K,
    TARGET_SELECTION_ROUND_ROBIN,
    TARGET_SELECTION_NEXT,
)


class TestEngineCapabilities(unittest.TestCase):
    """Tests for EngineCapabilities dataclass."""

    def test_default_capabilities(self):
        """Test default capability values."""
        caps = EngineCapabilities()
        self.assertTrue(caps.supports_logits)
        self.assertTrue(caps.supports_probabilities)
        self.assertFalse(caps.supports_attention)
        self.assertFalse(caps.supports_kv_cache)
        self.assertEqual(caps.default_device, "cpu")

    def test_capabilities_are_frozen(self):
        """Test that capabilities are immutable."""
        caps = EngineCapabilities()
        with self.assertRaises(Exception):  # FrozenInstanceError
            caps.supports_logits = False


class TestEngineInfo(unittest.TestCase):
    """Tests for EngineInfo dataclass."""

    def test_engine_info_properties(self):
        """Test that EngineInfo delegates to capabilities."""
        caps = EngineCapabilities(
            supports_logits=True,
            supports_attention=True,
            supports_kv_cache=True,
            supports_mind_meld=True,
        )
        info = EngineInfo(
            name="test",
            display_name="Test Engine",
            description="Test",
            capabilities=caps,
        )
        self.assertTrue(info.supports_logits)
        self.assertTrue(info.supports_attention)
        self.assertTrue(info.supports_kv_cache)
        self.assertTrue(info.supports_mind_meld)


class TestEngineRegistry(unittest.TestCase):
    """Tests for the ENGINES registry."""

    def test_registry_not_empty(self):
        """Test that registry has engines."""
        self.assertGreater(len(ENGINES), 0)

    def test_known_engines_present(self):
        """Test that expected engines are in registry."""
        expected = ["pytorch", "pytorch_cuda", "llamacpp", "ollama", "vllm"]
        for engine in expected:
            self.assertIn(engine, ENGINES, f"Engine {engine} not in registry")

    def test_all_engines_have_required_fields(self):
        """Test that all engines have required info."""
        for name, info in ENGINES.items():
            self.assertIsInstance(info.name, str)
            self.assertIsInstance(info.display_name, str)
            self.assertIsInstance(info.description, str)
            self.assertIsInstance(info.capabilities, EngineCapabilities)
            self.assertEqual(info.name, name)

    def test_pytorch_supports_attention(self):
        """Test that PyTorch engine supports attention."""
        pytorch = ENGINES.get("pytorch")
        self.assertIsNotNone(pytorch)
        self.assertTrue(pytorch.capabilities.supports_attention)

    def test_llamacpp_model_format(self):
        """Test that llamacpp uses GGUF format."""
        llamacpp = ENGINES.get("llamacpp")
        self.assertIsNotNone(llamacpp)
        self.assertEqual(llamacpp.capabilities.model_format, "gguf")


class TestRegistryFunctions(unittest.TestCase):
    """Tests for registry helper functions."""

    def test_get_engine_info_valid(self):
        """Test getting info for valid engine."""
        info = get_engine_info("pytorch")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "pytorch")

    def test_get_engine_info_case_insensitive(self):
        """Test that engine lookup is case-insensitive."""
        info = get_engine_info("PyTorch")
        self.assertIsNotNone(info)

    def test_get_engine_info_invalid(self):
        """Test getting info for invalid engine."""
        info = get_engine_info("nonexistent_engine")
        self.assertIsNone(info)

    def test_list_engines(self):
        """Test listing all engines."""
        engines = list_engines()
        self.assertIsInstance(engines, list)
        self.assertIn("pytorch", engines)

    def test_list_engines_with_capability(self):
        """Test filtering engines by capability."""
        # All engines with attention support
        with_attention = list_engines_with(supports_attention=True)
        self.assertIn("pytorch", with_attention)
        self.assertNotIn("llamacpp", with_attention)  # llamacpp doesn't support attention

    def test_list_engines_with_multiple_capabilities(self):
        """Test filtering by multiple capabilities."""
        engines = list_engines_with(supports_logits=True, supports_gpu=True)
        self.assertIn("pytorch_cuda", engines)

    def test_check_compatibility(self):
        """Test checking engine compatibility."""
        self.assertTrue(check_compatibility("pytorch", "logits"))
        self.assertTrue(check_compatibility("pytorch", "attention"))
        self.assertFalse(check_compatibility("llamacpp", "attention"))

    def test_check_compatibility_invalid_engine(self):
        """Test checking compatibility for invalid engine."""
        self.assertFalse(check_compatibility("nonexistent", "logits"))

    def test_get_mind_meld_compatible_engines(self):
        """Test getting Mind Meld compatible engines."""
        engines = get_mind_meld_compatible_engines()
        self.assertIsInstance(engines, list)
        # All major engines should be compatible
        self.assertIn("pytorch", engines)
        self.assertIn("llamacpp", engines)

    def test_get_engine_requirements(self):
        """Test getting engine requirements."""
        reqs = get_engine_requirements("pytorch")
        self.assertIn("torch", reqs)
        self.assertIn("transformers", reqs)

    def test_get_engine_requirements_invalid(self):
        """Test getting requirements for invalid engine."""
        reqs = get_engine_requirements("nonexistent")
        self.assertEqual(reqs, [])

    def test_format_engine_table(self):
        """Test formatting engine comparison table."""
        table = format_engine_table()
        self.assertIsInstance(table, str)
        self.assertIn("Engine", table)
        self.assertIn("Logits", table)
        self.assertIn("PyTorch", table)


class TestHelperConstants(unittest.TestCase):
    """Tests for helper constants in sampling_utils and meld_engine."""

    def test_fallback_top_k_defined(self):
        """Test that FALLBACK_TOP_K constant is defined."""
        from src.mind_meld.core.meld_engine import FALLBACK_TOP_K
        self.assertIsInstance(FALLBACK_TOP_K, int)
        self.assertGreater(FALLBACK_TOP_K, 0)
        self.assertEqual(FALLBACK_TOP_K, 100)

    def test_translation_logit_floor_defined(self):
        """Test that TRANSLATION_LOGIT_FLOOR is defined."""
        self.assertIsInstance(TRANSLATION_LOGIT_FLOOR, float)
        self.assertEqual(TRANSLATION_LOGIT_FLOOR, -10.0)

    def test_logit_floor_more_extreme(self):
        """Test that LOGIT_FLOOR is more extreme than TRANSLATION_LOGIT_FLOOR."""
        self.assertLess(LOGIT_FLOOR, TRANSLATION_LOGIT_FLOOR)
        self.assertEqual(LOGIT_FLOOR, -1e10)

    def test_logit_ceiling_positive(self):
        """Test that LOGIT_CEILING is positive."""
        self.assertGreater(LOGIT_CEILING, 0)
        self.assertEqual(LOGIT_CEILING, 1e10)

    def test_epsilon_small_positive(self):
        """Test that EPSILON is a small positive value."""
        self.assertGreater(EPSILON, 0)
        self.assertLess(EPSILON, 1e-5)

    def test_target_selection_constants(self):
        """Test that target selection constants are defined."""
        self.assertEqual(TARGET_SELECTION_ROUND_ROBIN, "round_robin")
        self.assertEqual(TARGET_SELECTION_NEXT, "next")

    def test_fallback_top_k_value(self):
        """Test that FALLBACK_TOP_K has expected value."""
        self.assertEqual(FALLBACK_TOP_K, 100)


class TestVocabularyTranslatorConstants(unittest.TestCase):
    """Tests for vocabulary translator constant imports."""

    def test_translator_uses_shared_constant(self):
        """Test that vocabulary translator imports from sampling_utils."""
        from src.mind_meld.translators.vocabulary_translator import VocabularyTranslator
        # Should match the sampling_utils constant
        self.assertEqual(VocabularyTranslator.DEFAULT_LOGIT_FLOOR, TRANSLATION_LOGIT_FLOOR)
        self.assertEqual(VocabularyTranslator.DEFAULT_LOGIT_FLOOR, -10.0)


if __name__ == "__main__":
    unittest.main()
