"""
Test MeldConfig Export/Import

Tests the configuration serialization features:
- MeldConfig.to_dict()
- MeldConfig.from_dict()
- MeldConfig.export_to_json()
- MeldConfig.load_from_json()
"""

import sys
import os

import unittest
import tempfile
import json

from src.mind_meld.core.config import (
    MeldConfig,
    SwapConfig,
    TranslationConfig,
    BridgeConfig,
    SwapStrategy,
    TranslationMode,
    VocabularyStrategy
)


class TestMeldConfigSerialization(unittest.TestCase):
    """Test configuration serialization and deserialization."""

    def test_to_dict(self):
        """Config should serialize to dictionary."""
        config = MeldConfig()
        config_dict = config.to_dict()

        self.assertIsInstance(config_dict, dict)
        self.assertIn('swap_config', config_dict)
        self.assertIn('translation_config', config_dict)
        self.assertIn('bridge_config', config_dict)
        self.assertIn('max_tokens', config_dict)
        self.assertIn('temperature', config_dict)

    def test_to_dict_preserves_values(self):
        """Serialized dict should preserve all config values."""
        config = MeldConfig(
            max_tokens=200,
            temperature=0.8,
            top_k=100,
            verbose=True
        )
        config_dict = config.to_dict()

        self.assertEqual(config_dict['max_tokens'], 200)
        self.assertEqual(config_dict['temperature'], 0.8)
        self.assertEqual(config_dict['top_k'], 100)
        self.assertEqual(config_dict['verbose'], True)

    def test_from_dict(self):
        """Should be able to reconstruct config from dict."""
        original = MeldConfig(max_tokens=150, temperature=0.9)
        config_dict = original.to_dict()

        restored = MeldConfig.from_dict(config_dict)

        self.assertEqual(restored.max_tokens, 150)
        self.assertEqual(restored.temperature, 0.9)

    def test_roundtrip_serialization(self):
        """Config should survive dict roundtrip unchanged."""
        original = MeldConfig(
            max_tokens=250,
            temperature=0.7,
            top_k=75,
            top_p=0.85,
            verbose=False
        )

        # to_dict -> from_dict
        restored = MeldConfig.from_dict(original.to_dict())

        self.assertEqual(restored.max_tokens, original.max_tokens)
        self.assertEqual(restored.temperature, original.temperature)
        self.assertEqual(restored.top_k, original.top_k)
        self.assertEqual(restored.top_p, original.top_p)
        self.assertEqual(restored.verbose, original.verbose)

    def test_export_to_json(self):
        """Should export config to JSON file."""
        config = MeldConfig(max_tokens=100, temperature=0.5)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            config.export_to_json(json_path)

            # Verify file exists and is valid JSON
            self.assertTrue(os.path.exists(json_path))

            with open(json_path, 'r') as f:
                data = json.load(f)

            self.assertIsInstance(data, dict)
            self.assertEqual(data['max_tokens'], 100)
            self.assertEqual(data['temperature'], 0.5)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_load_from_json(self):
        """Should load config from JSON file."""
        original = MeldConfig(max_tokens=300, temperature=0.6)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            original.export_to_json(json_path)
            loaded = MeldConfig.load_from_json(json_path)

            self.assertEqual(loaded.max_tokens, 300)
            self.assertEqual(loaded.temperature, 0.6)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_json_roundtrip(self):
        """Config should survive JSON file roundtrip."""
        original = MeldConfig(
            max_tokens=500,
            temperature=0.75,
            top_k=90,
            use_gpu=True,
            verbose=True
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            # Export and reload
            original.export_to_json(json_path)
            loaded = MeldConfig.load_from_json(json_path)

            # Verify all values preserved
            self.assertEqual(loaded.max_tokens, original.max_tokens)
            self.assertEqual(loaded.temperature, original.temperature)
            self.assertEqual(loaded.top_k, original.top_k)
            self.assertEqual(loaded.use_gpu, original.use_gpu)
            self.assertEqual(loaded.verbose, original.verbose)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_swap_strategy_serialization(self):
        """Swap strategy enum should serialize correctly."""
        config = MeldConfig()
        config.swap_config.strategy = SwapStrategy.CONFIDENCE_BASED

        config_dict = config.to_dict()

        self.assertEqual(
            config_dict['swap_config']['strategy'],
            'confidence'
        )

        # Roundtrip
        restored = MeldConfig.from_dict(config_dict)
        self.assertEqual(
            restored.swap_config.strategy,
            SwapStrategy.CONFIDENCE_BASED
        )

    def test_complex_config_serialization(self):
        """Complex nested config should serialize properly."""
        config = MeldConfig(
            swap_config=SwapConfig(
                strategy=SwapStrategy.PERPLEXITY_BASED,
                min_confidence=0.8,
                perplexity_threshold=20.0
            ),
            translation_config=TranslationConfig(
                mode=TranslationMode.INTERSECTION,
                vocabulary_strategy=VocabularyStrategy.RESTRICT_TO_INTERSECTION
            )
        )

        config_dict = config.to_dict()

        self.assertEqual(config_dict['swap_config']['strategy'], 'perplexity')
        self.assertEqual(config_dict['swap_config']['min_confidence'], 0.8)
        self.assertEqual(config_dict['swap_config']['perplexity_threshold'], 20.0)
        self.assertEqual(config_dict['translation_config']['mode'], 'intersection')


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""

    def test_validate_returns_list(self):
        """Validate should return a list."""
        config = MeldConfig()
        warnings = config.validate()
        self.assertIsInstance(warnings, list)

    def test_validate_low_vocab_overlap_warning(self):
        """Should warn when vocabulary overlap is very low."""
        config = MeldConfig()
        config.translation_config.min_vocab_overlap = 0.2
        warnings = config.validate()

        self.assertTrue(any("vocabulary overlap" in w.lower() for w in warnings))

    def test_validate_weighted_blend_without_weights(self):
        """Should warn when weighted blend has no weights."""
        config = MeldConfig()
        config.swap_config.strategy = SwapStrategy.WEIGHTED_BLEND
        config.swap_config.blend_weights = None
        warnings = config.validate()

        self.assertTrue(any("blend_weights" in w.lower() for w in warnings))

    def test_validate_projection_without_dim(self):
        """Should warn when projection mode has no projection_dim."""
        config = MeldConfig()
        config.translation_config.mode = TranslationMode.PROJECTION
        config.translation_config.projection_dim = None
        warnings = config.validate()

        self.assertTrue(any("projection_dim" in w.lower() for w in warnings))

    def test_validate_passes_for_good_config(self):
        """Should not warn for properly configured setup."""
        config = MeldConfig()
        config.translation_config.min_vocab_overlap = 0.8
        warnings = config.validate()

        # Should have no warnings about vocab overlap
        self.assertFalse(any("vocabulary overlap" in w.lower() for w in warnings))


class TestConfigEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_config(self):
        """Empty config should serialize and deserialize."""
        config = MeldConfig()
        config_dict = config.to_dict()
        restored = MeldConfig.from_dict(config_dict)

        self.assertIsNotNone(restored)

    def test_nonexistent_json_file(self):
        """Loading from nonexistent file should raise error."""
        with self.assertRaises(FileNotFoundError):
            MeldConfig.load_from_json('/nonexistent/path/config.json')


def run_tests():
    """Run all config tests."""
    print("=" * 80)
    print("Testing MeldConfig Export/Import")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
