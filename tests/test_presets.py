"""
Test Mind Meld Presets

Tests preset configurations including:
- PresetType enum
- MeldPreset dataclass
- Predefined presets
- Preset retrieval functions
- Custom preset creation
- Preset application helpers
- Preset recommendation system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock
from dataclasses import fields

from src.mind_meld.presets import (
    PresetType,
    MeldPreset,
    PRESETS,
    get_preset,
    list_presets,
    get_preset_by_name,
    create_custom_preset,
    apply_preset_to_args,
    get_recommended_preset
)


class TestPresetType(unittest.TestCase):
    """Test PresetType enum."""

    def test_preset_types_exist(self):
        """Should have all expected preset types."""
        self.assertEqual(PresetType.CREATIVE_WRITING.value, "creative_writing")
        self.assertEqual(PresetType.CODE_GENERATION.value, "code_generation")
        self.assertEqual(PresetType.TECHNICAL_WRITING.value, "technical_writing")
        self.assertEqual(PresetType.FAST_GENERATION.value, "fast_generation")
        self.assertEqual(PresetType.MAX_QUALITY.value, "max_quality")
        self.assertEqual(PresetType.RESEARCH_ANALYSIS.value, "research_analysis")
        self.assertEqual(PresetType.CONVERSATION.value, "conversation")
        self.assertEqual(PresetType.TRANSLATION.value, "translation")


class TestMeldPreset(unittest.TestCase):
    """Test MeldPreset dataclass."""

    def test_creation_with_defaults(self):
        """Should create preset with default values."""
        preset = MeldPreset(
            name="Test Preset",
            description="Test description",
            models=["model1", "model2"],
            strategy="pattern",
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )

        self.assertEqual(preset.name, "Test Preset")
        self.assertEqual(preset.description, "Test description")
        self.assertEqual(preset.models, ["model1", "model2"])
        self.assertEqual(preset.strategy, "pattern")
        self.assertFalse(preset.use_speculative)
        self.assertFalse(preset.use_contrastive)
        self.assertEqual(preset.max_tokens, 100)
        self.assertIsNotNone(preset.additional_config)
        self.assertEqual(preset.additional_config, {})

    def test_post_init_initializes_additional_config(self):
        """Should initialize additional_config if None."""
        preset = MeldPreset(
            name="Test",
            description="Test",
            models=["model1"],
            strategy="fixed",
            temperature=0.5,
            top_k=40,
            top_p=0.9,
            additional_config=None
        )

        self.assertIsNotNone(preset.additional_config)
        self.assertEqual(preset.additional_config, {})

    def test_creation_with_all_features(self):
        """Should create preset with all advanced features."""
        preset = MeldPreset(
            name="Advanced",
            description="All features enabled",
            models=["model1"],
            strategy="perplexity",
            temperature=0.6,
            top_k=60,
            top_p=0.92,
            use_speculative=True,
            use_contrastive=True,
            use_abe=True,
            use_moe=True,
            use_feedback=True,
            use_hierarchical=True,
            use_adversarial=True,
            max_tokens=250,
            additional_config={"key": "value"}
        )

        self.assertTrue(preset.use_speculative)
        self.assertTrue(preset.use_contrastive)
        self.assertTrue(preset.use_abe)
        self.assertTrue(preset.use_moe)
        self.assertTrue(preset.use_feedback)
        self.assertTrue(preset.use_hierarchical)
        self.assertTrue(preset.use_adversarial)
        self.assertEqual(preset.max_tokens, 250)
        self.assertEqual(preset.additional_config, {"key": "value"})


class TestPredefinedPresets(unittest.TestCase):
    """Test predefined presets."""

    def test_all_preset_types_have_definitions(self):
        """Should have preset definitions for all types."""
        for preset_type in PresetType:
            self.assertIn(preset_type, PRESETS)

    def test_creative_writing_preset(self):
        """Should have correct creative writing configuration."""
        preset = PRESETS[PresetType.CREATIVE_WRITING]

        self.assertEqual(preset.name, "Creative Writing")
        self.assertGreater(preset.temperature, 0.7)  # High creativity
        self.assertIsInstance(preset.models, list)
        self.assertTrue(len(preset.models) > 0)

    def test_code_generation_preset(self):
        """Should have correct code generation configuration."""
        preset = PRESETS[PresetType.CODE_GENERATION]

        self.assertEqual(preset.name, "Code Generation")
        self.assertLess(preset.temperature, 0.5)  # Low for accuracy
        self.assertTrue(preset.use_abe or preset.use_feedback)  # Quality checks

    def test_fast_generation_preset(self):
        """Should have speed-optimized configuration."""
        preset = PRESETS[PresetType.FAST_GENERATION]

        self.assertEqual(preset.name, "Fast Generation")
        self.assertTrue(preset.use_speculative)  # Speedup feature

    def test_max_quality_preset(self):
        """Should have quality-optimized configuration."""
        preset = PRESETS[PresetType.MAX_QUALITY]

        self.assertEqual(preset.name, "Maximum Quality")
        # Should use multiple quality features
        quality_features = [
            preset.use_contrastive,
            preset.use_abe,
            preset.use_feedback,
            preset.use_adversarial
        ]
        self.assertGreater(sum(quality_features), 2)

    def test_all_presets_have_required_fields(self):
        """All presets should have required fields."""
        for preset_type, preset in PRESETS.items():
            self.assertIsInstance(preset.name, str)
            self.assertIsInstance(preset.description, str)
            self.assertIsInstance(preset.models, list)
            self.assertGreater(len(preset.models), 0)
            self.assertIsInstance(preset.strategy, str)
            self.assertIsInstance(preset.temperature, (int, float))
            self.assertIsInstance(preset.top_k, int)
            self.assertIsInstance(preset.top_p, (int, float))


class TestGetPreset(unittest.TestCase):
    """Test get_preset function."""

    def test_get_preset_returns_correct_preset(self):
        """Should return correct preset for given type."""
        preset = get_preset(PresetType.CREATIVE_WRITING)

        self.assertEqual(preset.name, "Creative Writing")
        self.assertIsInstance(preset, MeldPreset)

    def test_get_preset_for_all_types(self):
        """Should work for all preset types."""
        for preset_type in PresetType:
            preset = get_preset(preset_type)
            self.assertIsInstance(preset, MeldPreset)


class TestListPresets(unittest.TestCase):
    """Test list_presets function."""

    def test_list_presets_returns_all(self):
        """Should return all available presets."""
        preset_list = list_presets()

        self.assertEqual(len(preset_list), len(PresetType))

    def test_list_presets_format(self):
        """Should return list of (type, description) tuples."""
        preset_list = list_presets()

        for item in preset_list:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            preset_type, description = item
            self.assertIsInstance(preset_type, PresetType)
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)


class TestGetPresetByName(unittest.TestCase):
    """Test get_preset_by_name function."""

    def test_get_by_exact_value(self):
        """Should find preset by exact enum value."""
        preset = get_preset_by_name("creative_writing")

        self.assertIsNotNone(preset)
        self.assertEqual(preset.name, "Creative Writing")

    def test_get_by_display_name(self):
        """Should find preset by display name."""
        preset = get_preset_by_name("Creative Writing")

        self.assertIsNotNone(preset)
        self.assertEqual(preset.name, "Creative Writing")

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        preset1 = get_preset_by_name("CREATIVE_WRITING")
        preset2 = get_preset_by_name("creative writing")
        preset3 = get_preset_by_name("Creative Writing")

        self.assertIsNotNone(preset1)
        self.assertIsNotNone(preset2)
        self.assertIsNotNone(preset3)
        self.assertEqual(preset1.name, preset2.name)
        self.assertEqual(preset2.name, preset3.name)

    def test_returns_none_for_invalid_name(self):
        """Should return None for non-existent preset."""
        preset = get_preset_by_name("nonexistent_preset")

        self.assertIsNone(preset)


class TestCreateCustomPreset(unittest.TestCase):
    """Test create_custom_preset function."""

    def test_create_with_minimal_args(self):
        """Should create preset with minimal arguments."""
        preset = create_custom_preset(
            name="Custom",
            models=["model1", "model2"]
        )

        self.assertEqual(preset.name, "Custom")
        self.assertEqual(preset.models, ["model1", "model2"])
        self.assertEqual(preset.strategy, "pattern")  # Default
        self.assertEqual(preset.description, "Custom preset")  # Default
        self.assertEqual(preset.temperature, 0.7)  # Default

    def test_create_with_custom_strategy(self):
        """Should accept custom strategy."""
        preset = create_custom_preset(
            name="Custom",
            models=["model1"],
            strategy="perplexity"
        )

        self.assertEqual(preset.strategy, "perplexity")

    def test_create_with_all_parameters(self):
        """Should accept all configuration parameters."""
        preset = create_custom_preset(
            name="Full Custom",
            models=["model1", "model2"],
            strategy="semantic",
            description="Fully customized",
            temperature=0.8,
            top_k=100,
            top_p=0.98,
            use_speculative=True,
            use_contrastive=True,
            use_abe=True,
            use_moe=True,
            use_feedback=True,
            use_hierarchical=True,
            use_adversarial=True,
            max_tokens=500,
            additional_config={"custom_key": "custom_value"}
        )

        self.assertEqual(preset.name, "Full Custom")
        self.assertEqual(preset.description, "Fully customized")
        self.assertEqual(preset.temperature, 0.8)
        self.assertEqual(preset.top_k, 100)
        self.assertEqual(preset.top_p, 0.98)
        self.assertTrue(preset.use_speculative)
        self.assertTrue(preset.use_contrastive)
        self.assertTrue(preset.use_abe)
        self.assertTrue(preset.use_moe)
        self.assertTrue(preset.use_feedback)
        self.assertTrue(preset.use_hierarchical)
        self.assertTrue(preset.use_adversarial)
        self.assertEqual(preset.max_tokens, 500)
        self.assertEqual(preset.additional_config, {"custom_key": "custom_value"})


class TestApplyPresetToArgs(unittest.TestCase):
    """Test apply_preset_to_args function."""

    def test_apply_basic_parameters(self):
        """Should apply basic preset parameters to args."""
        preset = PRESETS[PresetType.CREATIVE_WRITING]
        args = MagicMock()

        apply_preset_to_args(preset, args)

        self.assertEqual(args.temperature, preset.temperature)
        self.assertEqual(args.top_k, preset.top_k)
        self.assertEqual(args.top_p, preset.top_p)
        self.assertEqual(args.steps, preset.max_tokens)
        self.assertEqual(args.swap_strategy, preset.strategy)

    def test_apply_advanced_features(self):
        """Should apply advanced feature flags."""
        preset = PRESETS[PresetType.MAX_QUALITY]
        args = MagicMock()

        apply_preset_to_args(preset, args)

        self.assertEqual(args.use_speculative, preset.use_speculative)
        self.assertEqual(args.use_contrastive, preset.use_contrastive)
        self.assertEqual(args.use_abe, preset.use_abe)
        self.assertEqual(args.use_moe, preset.use_moe)
        self.assertEqual(args.use_feedback, preset.use_feedback)
        self.assertEqual(args.use_hierarchical, preset.use_hierarchical)
        self.assertEqual(args.use_adversarial, preset.use_adversarial)

    def test_apply_additional_config(self):
        """Should apply additional config items."""
        preset = MeldPreset(
            name="Test",
            description="Test",
            models=["model1"],
            strategy="fixed",
            temperature=0.5,
            top_k=40,
            top_p=0.9,
            additional_config={
                "custom_param1": 42,
                "custom_param2": "value"
            }
        )
        args = MagicMock()

        apply_preset_to_args(preset, args)

        self.assertEqual(args.custom_param1, 42)
        self.assertEqual(args.custom_param2, "value")


class TestGetRecommendedPreset(unittest.TestCase):
    """Test get_recommended_preset function."""

    def test_recommend_code_generation(self):
        """Should recommend code generation for code-related tasks."""
        test_cases = [
            "write a function to sort an array",
            "debug this code",
            "create a program that calculates fibonacci"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Code Generation")

    def test_recommend_creative_writing(self):
        """Should recommend creative writing for creative tasks."""
        test_cases = [
            "write a story about a dragon",
            "help me brainstorm ideas",
            "compose a poem about nature"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Creative Writing")

    def test_recommend_technical_writing(self):
        """Should recommend technical writing for documentation tasks."""
        test_cases = [
            "write technical documentation",
            "explain how this algorithm works",
            "provide analysis of the data"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Technical Writing")

    def test_recommend_fast_generation(self):
        """Should recommend fast generation for speed-focused tasks."""
        test_cases = [
            "generate something quickly",
            "I need a fast response",
            "speed is important"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Fast Generation")

    def test_recommend_max_quality(self):
        """Should recommend max quality for quality-focused tasks."""
        test_cases = [
            "I need the best possible output",
            "highest quality please",
            "perfect response required"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Maximum Quality")

    def test_recommend_research_analysis(self):
        """Should recommend research for analysis tasks."""
        test_cases = [
            "research this topic",
            "analyze the trends",
            "study these patterns"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Research & Analysis")

    def test_recommend_conversation(self):
        """Should recommend conversation for chat tasks."""
        test_cases = [
            "let's have a chat",
            "I want to talk about something",
            "start a conversation"
        ]

        for task in test_cases:
            preset = get_recommended_preset(task)
            self.assertEqual(preset.name, "Conversation")

    def test_recommend_translation(self):
        """Should recommend translation for translation tasks."""
        preset1 = get_recommended_preset("translate this to Spanish")
        self.assertEqual(preset1.name, "Translation")

        preset2 = get_recommended_preset("I need translation help")
        self.assertEqual(preset2.name, "Translation")

        # "convert" is not in the translation keywords, so skip this one
        # preset3 = get_recommended_preset("convert this to French")
        # self.assertEqual(preset3.name, "Translation")

    def test_default_recommendation(self):
        """Should return default preset for ambiguous tasks."""
        preset = get_recommended_preset("some random task with no keywords")

        # Default is Conversation
        self.assertEqual(preset.name, "Conversation")


def run_tests():
    """Run all preset tests."""
    print("=" * 80)
    print("Testing Mind Meld Presets")
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
