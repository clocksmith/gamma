"""Edge case tests for Model Compatibility Validation.

Tests for the ModelCompatibilityValidator including:
- Architecture detection edge cases
- Vocabulary overlap estimation
- KV cache bridging compatibility
- Ensemble validation
- Optimal swap ordering
"""

import unittest
from unittest.mock import MagicMock, PropertyMock

from src.mind_meld.core.compatibility import (
    ModelCompatibilityValidator,
    CompatibilityLevel,
    CompatibilityReport,
)


class MockModelConfig:
    """Mock model configuration for testing."""

    def __init__(
        self,
        model_type: str = "llama",
        vocab_size: int = 32000,
        hidden_size: int = 4096,
        num_hidden_layers: int = 32,
        num_attention_heads: int = 32,
        architectures: list = None
    ):
        self.model_type = model_type
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.architectures = architectures or [f"{model_type}ForCausalLM"]


class MockEngine:
    """Mock LLM engine for testing compatibility."""

    def __init__(
        self,
        model_name: str,
        config: MockModelConfig = None,
        vocab: dict = None,
        supports_bridging: bool = True
    ):
        self.model_name = model_name
        self._config = config or MockModelConfig()
        self._vocab = vocab or {f"token_{i}": i for i in range(100)}
        self._supports_bridging_flag = supports_bridging
        self.model = MagicMock()
        self.model.config = self._config
        self.tokenizer = MagicMock()
        self.tokenizer.get_vocab.return_value = self._vocab

    def get_vocabulary_size(self) -> int:
        return self._config.vocab_size

    def get_num_layers(self) -> int:
        return self._config.num_hidden_layers

    def get_vocab(self) -> dict:
        return self._vocab

    def _supports_cache_bridging(self) -> bool:
        return self._supports_bridging_flag


class TestCompatibilityValidatorEdgeCases(unittest.TestCase):
    """Edge case tests for ModelCompatibilityValidator."""

    def setUp(self):
        self.validator = ModelCompatibilityValidator(verbose=False)

    def test_identical_models(self):
        """Test compatibility between identical models."""
        config = MockModelConfig()
        engine1 = MockEngine("llama-7b", config)
        engine2 = MockEngine("llama-7b", config)

        report = self.validator.validate_pair(engine1, engine2)

        self.assertEqual(report.level, CompatibilityLevel.EXCELLENT)
        self.assertGreater(report.overall_score, 0.85)
        self.assertTrue(report.architecture_match)
        self.assertTrue(report.hidden_size_match)
        self.assertTrue(report.num_layers_match)
        self.assertTrue(report.num_heads_match)

    def test_same_architecture_different_sizes(self):
        """Test compatibility between same architecture, different sizes."""
        config1 = MockModelConfig(
            model_type="llama",
            hidden_size=4096,
            num_hidden_layers=32
        )
        config2 = MockModelConfig(
            model_type="llama",
            hidden_size=2048,
            num_hidden_layers=24
        )

        engine1 = MockEngine("llama-7b", config1)
        engine2 = MockEngine("llama-2b", config2)

        report = self.validator.validate_pair(engine1, engine2)

        self.assertTrue(report.architecture_match)
        self.assertFalse(report.hidden_size_match)
        self.assertFalse(report.num_layers_match)
        self.assertFalse(report.kv_cache_bridgeable)
        # Should still be at least FAIR due to same architecture
        self.assertIn(report.level, [CompatibilityLevel.GOOD, CompatibilityLevel.FAIR])

    def test_different_architectures(self):
        """Test compatibility between different architectures."""
        config1 = MockModelConfig(model_type="llama")
        config2 = MockModelConfig(model_type="gpt2")

        engine1 = MockEngine("llama-7b", config1)
        engine2 = MockEngine("gpt2-xl", config2)

        report = self.validator.validate_pair(engine1, engine2)

        self.assertFalse(report.architecture_match)
        self.assertIn("Different architectures", "\n".join(report.warnings))

    def test_compatible_architecture_families(self):
        """Test that related architectures are recognized as compatible."""
        config1 = MockModelConfig(model_type="llama")
        config2 = MockModelConfig(model_type="mistral")

        engine1 = MockEngine("llama-7b", config1)
        engine2 = MockEngine("mistral-7b", config2)

        # Both are in the llama family
        arch1 = self.validator._detect_architecture(engine1, config1)
        arch2 = self.validator._detect_architecture(engine2, config2)

        self.assertTrue(self.validator._architectures_compatible(arch1, arch2))

    def test_unknown_architecture(self):
        """Test handling of unknown architectures."""
        config = MockModelConfig(model_type="custom_model")
        engine = MockEngine("custom-model", config)

        arch = self.validator._detect_architecture(engine, config)

        # Should fall back to model_type
        self.assertEqual(arch, "custom_model")

    def test_kv_cache_bridging_requirements(self):
        """Test KV cache bridging requires exact match."""
        config = MockModelConfig()

        # Both support bridging but have different dimensions
        engine1 = MockEngine("model1", config, supports_bridging=True)
        config2 = MockModelConfig(hidden_size=2048)
        engine2 = MockEngine("model2", config2, supports_bridging=True)

        report = self.validator.validate_pair(engine1, engine2)

        self.assertFalse(report.kv_cache_bridgeable)

    def test_no_bridging_support(self):
        """Test when engines don't support bridging."""
        config = MockModelConfig()
        engine1 = MockEngine("model1", config, supports_bridging=False)
        engine2 = MockEngine("model2", config, supports_bridging=False)

        report = self.validator.validate_pair(engine1, engine2)

        self.assertFalse(report.kv_cache_bridgeable)

    def test_vocab_overlap_estimation_with_actual_vocab(self):
        """Test vocabulary overlap with actual vocabulary data."""
        # Create engines with overlapping vocabularies
        vocab1 = {"hello": 0, "world": 1, "test": 2}
        vocab2 = {"hello": 0, "world": 1, "other": 2}

        engine1 = MockEngine("model1", vocab=vocab1)
        engine2 = MockEngine("model2", vocab=vocab2)

        overlap = self.validator._estimate_vocab_overlap(engine1, engine2)

        # 2 common out of 4 unique = 0.5
        self.assertAlmostEqual(overlap, 0.5, places=2)

    def test_vocab_overlap_fallback(self):
        """Test vocabulary overlap estimation when vocab not available."""
        config1 = MockModelConfig(model_type="llama")
        config2 = MockModelConfig(model_type="llama")

        engine1 = MockEngine("llama1", config1)
        engine2 = MockEngine("llama2", config2)

        # Remove vocab access
        engine1.tokenizer.get_vocab.side_effect = RuntimeError("No vocab")
        engine2.tokenizer.get_vocab.side_effect = RuntimeError("No vocab")

        overlap = self.validator._estimate_vocab_overlap(engine1, engine2)

        # Same architecture should estimate high overlap
        self.assertGreater(overlap, 0.5)

    def test_warnings_and_suggestions(self):
        """Test that appropriate warnings and suggestions are generated."""
        config1 = MockModelConfig(
            model_type="llama",
            hidden_size=4096,
            num_hidden_layers=32
        )
        config2 = MockModelConfig(
            model_type="gpt2",
            hidden_size=1024,
            num_hidden_layers=12
        )

        engine1 = MockEngine("llama-7b", config1)
        engine2 = MockEngine("gpt2", config2)

        report = self.validator.validate_pair(engine1, engine2)

        # Should have warnings about mismatches
        self.assertGreater(len(report.warnings), 0)
        # Should have suggestions for improvements
        self.assertGreater(len(report.suggestions), 0)

    def test_score_to_level_boundaries(self):
        """Test boundary conditions for score to level conversion."""
        # Test exact boundaries
        self.assertEqual(
            self.validator._score_to_level(0.85),
            CompatibilityLevel.EXCELLENT
        )
        self.assertEqual(
            self.validator._score_to_level(0.84),
            CompatibilityLevel.GOOD
        )
        self.assertEqual(
            self.validator._score_to_level(0.65),
            CompatibilityLevel.GOOD
        )
        self.assertEqual(
            self.validator._score_to_level(0.64),
            CompatibilityLevel.FAIR
        )
        self.assertEqual(
            self.validator._score_to_level(0.45),
            CompatibilityLevel.FAIR
        )
        self.assertEqual(
            self.validator._score_to_level(0.44),
            CompatibilityLevel.POOR
        )
        self.assertEqual(
            self.validator._score_to_level(0.25),
            CompatibilityLevel.POOR
        )
        self.assertEqual(
            self.validator._score_to_level(0.24),
            CompatibilityLevel.INCOMPATIBLE
        )


class TestEnsembleValidation(unittest.TestCase):
    """Tests for ensemble validation."""

    def setUp(self):
        self.validator = ModelCompatibilityValidator(verbose=False)

    def test_all_compatible_ensemble(self):
        """Test validation of fully compatible ensemble."""
        config = MockModelConfig()
        engines = [
            MockEngine("model1", config),
            MockEngine("model2", config),
            MockEngine("model3", config),
        ]

        all_compatible, reports = self.validator.validate_ensemble(engines)

        self.assertTrue(all_compatible)
        # N choose 2 = 3 pairs
        self.assertEqual(len(reports), 3)

    def test_partially_compatible_ensemble(self):
        """Test validation with some incompatible pairs."""
        config_llama = MockModelConfig(model_type="llama")
        config_gpt = MockModelConfig(model_type="gpt2", hidden_size=1024)

        engines = [
            MockEngine("llama1", config_llama),
            MockEngine("llama2", config_llama),
            MockEngine("gpt2", config_gpt),
        ]

        all_compatible, reports = self.validator.validate_ensemble(engines)

        # Llama models are compatible with each other
        # GPT2 is less compatible with Llama
        self.assertEqual(len(reports), 3)

    def test_two_model_ensemble(self):
        """Test ensemble with exactly two models."""
        config = MockModelConfig()
        engines = [
            MockEngine("model1", config),
            MockEngine("model2", config),
        ]

        all_compatible, reports = self.validator.validate_ensemble(engines)

        self.assertEqual(len(reports), 1)


class TestOptimalSwapOrdering(unittest.TestCase):
    """Tests for optimal swap order calculation."""

    def setUp(self):
        self.validator = ModelCompatibilityValidator(verbose=False)

    def test_two_models_order(self):
        """Test ordering with two models."""
        config = MockModelConfig()
        engines = [
            MockEngine("model0", config),
            MockEngine("model1", config),
        ]

        order = self.validator.get_best_swap_order(engines)

        self.assertEqual(order, [0, 1])

    def test_three_models_order(self):
        """Test ordering with three models."""
        # Create models with varying compatibility
        config_base = MockModelConfig()
        config_similar = MockModelConfig(hidden_size=4096)
        config_different = MockModelConfig(hidden_size=1024)

        engines = [
            MockEngine("base", config_base),
            MockEngine("similar", config_similar),
            MockEngine("different", config_different),
        ]

        order = self.validator.get_best_swap_order(engines)

        # Should start with model 0
        self.assertEqual(order[0], 0)
        # Should include all models
        self.assertEqual(sorted(order), [0, 1, 2])


class TestCompatibilityReport(unittest.TestCase):
    """Tests for CompatibilityReport."""

    def test_report_string_representation(self):
        """Test string representation of report."""
        report = CompatibilityReport(
            source_model="model1",
            target_model="model2",
            level=CompatibilityLevel.GOOD,
            overall_score=0.75,
            architecture_match=True,
            architecture_source="llama",
            architecture_target="llama",
            vocab_overlap_ratio=0.8,
            vocab_size_source=32000,
            vocab_size_target=32000,
            hidden_size_match=True,
            hidden_size_source=4096,
            hidden_size_target=4096,
            num_layers_match=True,
            num_layers_source=32,
            num_layers_target=32,
            num_heads_match=True,
            num_heads_source=32,
            num_heads_target=32,
            kv_cache_bridgeable=True,
            warnings=["Test warning"],
            suggestions=["Test suggestion"]
        )

        report_str = str(report)

        self.assertIn("model1", report_str)
        self.assertIn("model2", report_str)
        self.assertIn("good", report_str.lower())
        self.assertIn("0.75", report_str)
        self.assertIn("Test warning", report_str)
        self.assertIn("Test suggestion", report_str)


if __name__ == "__main__":
    unittest.main()
