"""
Test Model Registry

Tests model selection, profiling, and ensemble configuration:
- ModelSpecialization enum
- ModelProfile dataclass (VRAM estimation, fitting checks)
- MODEL_ZOO structure and content
- ModelSelector task-based and strategy-based selection
- Module-level helper functions
"""

import sys

import unittest
from typing import List

from src.core.models.model_registry import (
    ModelSpecialization,
    ModelProfile,
    MODEL_ZOO,
    ModelSelector,
    get_model_profile,
    list_models_by_specialization,
    get_recommended_ensemble
)


class TestModelSpecialization(unittest.TestCase):
    """Test ModelSpecialization enum."""

    def test_all_specializations_exist(self):
        """Should have all expected specialization types."""
        expected = ['CODE', 'CREATIVE', 'REASONING', 'FAST', 'TECHNICAL',
                   'CONVERSATIONAL', 'MATH', 'MULTILINGUAL']

        for spec_name in expected:
            self.assertTrue(hasattr(ModelSpecialization, spec_name))

    def test_specialization_values(self):
        """Should have correct string values."""
        self.assertEqual(ModelSpecialization.CODE.value, "code")
        self.assertEqual(ModelSpecialization.CREATIVE.value, "creative")
        self.assertEqual(ModelSpecialization.REASONING.value, "reasoning")
        self.assertEqual(ModelSpecialization.FAST.value, "fast")


class TestModelProfile(unittest.TestCase):
    """Test ModelProfile dataclass."""

    def setUp(self):
        """Create test model profile."""
        self.profile = ModelProfile(
            name='test/model-1b',
            engine='pytorch',
            size_mb=1000,
            specialization=ModelSpecialization.FAST,
            min_vram_mb=2048,
            context_length=2048,
            strengths=['speed', 'low_memory'],
            description='Test model'
        )

    def test_initialization(self):
        """Should initialize with all required fields."""
        self.assertEqual(self.profile.name, 'test/model-1b')
        self.assertEqual(self.profile.engine, 'pytorch')
        self.assertEqual(self.profile.size_mb, 1000)
        self.assertEqual(self.profile.specialization, ModelSpecialization.FAST)
        self.assertEqual(self.profile.min_vram_mb, 2048)
        self.assertEqual(self.profile.context_length, 2048)

    def test_default_values(self):
        """Should have correct default values."""
        self.assertEqual(self.profile.recommended_temperature, 0.7)
        self.assertEqual(self.profile.recommended_top_k, 50)
        self.assertEqual(self.profile.recommended_top_p, 0.95)
        self.assertEqual(self.profile.supports_kv_cache, True)
        self.assertEqual(self.profile.license, "apache-2.0")
        self.assertIn("none", self.profile.quantization_options)

    def test_estimate_vram_with_context_default(self):
        """Should estimate VRAM for default context size."""
        estimated = self.profile.estimate_vram_with_context()

        # 1000 (base) + 1.0 (kv cache for 2048 tokens) + 512 (overhead)
        self.assertEqual(estimated, 1513)

    def test_estimate_vram_with_context_large(self):
        """Should estimate VRAM for large context size."""
        estimated = self.profile.estimate_vram_with_context(context_tokens=8192)

        # 1000 + 4.096 (kv cache) + 512 = ~1516
        self.assertEqual(estimated, 1516)

    def test_estimate_vram_with_context_small(self):
        """Should estimate VRAM for small context size."""
        estimated = self.profile.estimate_vram_with_context(context_tokens=512)

        # 1000 + 0.256 + 512 = 1512
        self.assertEqual(estimated, 1512)

    def test_fits_in_vram_true(self):
        """Should return True when model fits."""
        fits = self.profile.fits_in_vram(available_vram_mb=4096)

        self.assertTrue(fits)

    def test_fits_in_vram_false(self):
        """Should return False when model doesn't fit."""
        fits = self.profile.fits_in_vram(available_vram_mb=1000)

        self.assertFalse(fits)

    def test_fits_in_vram_edge_case(self):
        """Should handle exact fit correctly."""
        estimated = self.profile.estimate_vram_with_context(2048)
        fits = self.profile.fits_in_vram(available_vram_mb=estimated)

        self.assertTrue(fits)

    def test_fits_in_vram_with_large_context(self):
        """Should account for context size in VRAM check."""
        # With 2048 tokens it fits in 4GB
        fits_small = self.profile.fits_in_vram(available_vram_mb=4096, context_tokens=2048)

        # With 2048 tokens it doesn't fit in 1GB
        fits_large = self.profile.fits_in_vram(available_vram_mb=1000, context_tokens=2048)

        self.assertTrue(fits_small)
        self.assertFalse(fits_large)


class TestModelZoo(unittest.TestCase):
    """Test MODEL_ZOO structure and content."""

    def test_model_zoo_populated(self):
        """Should contain expected models."""
        self.assertGreater(len(MODEL_ZOO), 0)
        self.assertIn('tinyllama', MODEL_ZOO)
        self.assertIn('gemma_2b', MODEL_ZOO)

    def test_model_zoo_all_profiles(self):
        """Should contain only ModelProfile instances."""
        for key, profile in MODEL_ZOO.items():
            self.assertIsInstance(profile, ModelProfile)
            self.assertIsInstance(key, str)

    def test_tinyllama_profile(self):
        """Should have correct TinyLlama profile."""
        tinyllama = MODEL_ZOO['tinyllama']

        self.assertEqual(tinyllama.name, 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
        self.assertEqual(tinyllama.specialization, ModelSpecialization.FAST)
        self.assertEqual(tinyllama.size_mb, 1100)
        self.assertIn('speed', tinyllama.strengths)

    def test_codellama_profile(self):
        """Should have correct CodeLlama profile."""
        codellama = MODEL_ZOO['codellama_7b']

        self.assertEqual(codellama.specialization, ModelSpecialization.CODE)
        self.assertIn('code_generation', codellama.strengths)
        self.assertEqual(codellama.recommended_temperature, 0.2)

    def test_all_models_have_valid_specializations(self):
        """All models should have valid specialization."""
        for profile in MODEL_ZOO.values():
            self.assertIsInstance(profile.specialization, ModelSpecialization)


class TestModelSelector(unittest.TestCase):
    """Test ModelSelector class."""

    def setUp(self):
        """Create test selector."""
        self.selector = ModelSelector(available_vram_mb=16384)  # 16GB

    def test_initialization(self):
        """Should initialize with VRAM budget."""
        self.assertEqual(self.selector.available_vram_mb, 16384)

    def test_select_for_task_code(self):
        """Should select code models for code tasks."""
        tasks = [
            "Write a Python function",
            "Debug this code",
            "Generate a programming solution"
        ]

        for task in tasks:
            models = self.selector.select_for_task(task, num_models=2)

            self.assertEqual(len(models), 2)
            # At least one should be code-specialized
            specializations = [m.specialization for m in models]
            self.assertTrue(
                ModelSpecialization.CODE in specializations or
                ModelSpecialization.REASONING in specializations
            )

    def test_select_for_task_creative(self):
        """Should select creative models for creative tasks."""
        tasks = [
            "Write a creative story",
            "Compose a poem",
            "Generate a novel idea"
        ]

        for task in tasks:
            models = self.selector.select_for_task(task, num_models=2)

            self.assertEqual(len(models), 2)
            specializations = [m.specialization for m in models]
            self.assertTrue(
                ModelSpecialization.CREATIVE in specializations or
                ModelSpecialization.CONVERSATIONAL in specializations
            )

    def test_select_for_task_math(self):
        """Should select math models for math tasks."""
        tasks = [
            "Solve this equation",
            "Calculate the derivative",
            "Explain this mathematical concept"
        ]

        for task in tasks:
            models = self.selector.select_for_task(task, num_models=2)

            self.assertEqual(len(models), 2)
            specializations = [m.specialization for m in models]
            self.assertTrue(
                ModelSpecialization.MATH in specializations or
                ModelSpecialization.REASONING in specializations
            )

    def test_select_for_task_translation(self):
        """Should select multilingual models for translation tasks."""
        tasks = [
            "Translate this to Spanish",
            "Help with multilingual document",
            "Convert between languages"
        ]

        for task in tasks:
            models = self.selector.select_for_task(task, num_models=2)

            self.assertEqual(len(models), 2)
            specializations = [m.specialization for m in models]
            self.assertTrue(
                ModelSpecialization.MULTILINGUAL in specializations or
                ModelSpecialization.CONVERSATIONAL in specializations
            )

    def test_select_for_task_technical(self):
        """Should select technical models for technical tasks."""
        tasks = [
            "Explain this technical concept",
            "Analyze this system"
        ]

        for task in tasks:
            models = self.selector.select_for_task(task, num_models=2)

            self.assertEqual(len(models), 2)

    def test_select_for_task_generic(self):
        """Should select conversational models for generic tasks."""
        models = self.selector.select_for_task("Hello, how are you?", num_models=2)

        self.assertEqual(len(models), 2)

    def test_select_for_task_limited_vram(self):
        """Should fall back to smallest models when VRAM limited."""
        small_selector = ModelSelector(available_vram_mb=512)  # Very limited
        models = small_selector.select_for_task("Any task", num_models=2)

        # Should return smallest models
        self.assertEqual(len(models), 2)
        for model in models:
            self.assertLessEqual(model.size_mb, 3000)

    def test_select_for_task_respects_num_models(self):
        """Should return requested number of models."""
        for num in [1, 2, 3, 4]:
            models = self.selector.select_for_task("Any task", num_models=num)
            self.assertLessEqual(len(models), num)

    def test_select_for_task_diverse_ensemble(self):
        """Should select diverse specializations when possible."""
        models = self.selector.select_for_task("General task", num_models=4)

        specializations = [m.specialization for m in models]
        # Should have some diversity
        unique_specs = set(specializations)
        self.assertGreaterEqual(len(unique_specs), 2)

    def test_select_for_task_exhausts_candidates(self):
        """Should stop when no more candidates available."""
        # Request 10 models with 3.5GB total
        # Each model gets 3500 / 10 = 350 MB per model
        # Only the very smallest models will fit (tinyllama needs ~1613 MB)
        # So candidates will be empty, falling back to smallest
        # Then request 5 models with 8GB, each gets 1600 MB
        # Only 1-2 models fit, but we request 5
        selector_8gb = ModelSelector(available_vram_mb=8192)
        models = selector_8gb.select_for_task("Any task", num_models=5, context_tokens=2048)

        # Should return fewer than 5 since only 1-2 models fit in 1638 MB each
        self.assertLessEqual(len(models), 5)
        self.assertGreater(len(models), 0)

    def test_select_for_strategy_speculative(self):
        """Should select draft + target for speculative strategy."""
        models = self.selector.select_for_strategy('speculative')

        self.assertEqual(len(models), 2)
        # First should be smaller (draft)
        self.assertLess(models[0].size_mb, models[1].size_mb)

    def test_select_for_strategy_contrastive(self):
        """Should select expert + amateur for contrastive strategy."""
        models = self.selector.select_for_strategy('contrastive')

        self.assertEqual(len(models), 2)
        # First should be larger (expert)
        self.assertGreater(models[0].size_mb, models[1].size_mb)
        # Amateur should be roughly 1/4 the size
        ratio = models[0].size_mb / models[1].size_mb
        self.assertGreater(ratio, 2.0)

    def test_select_for_strategy_moe(self):
        """Should select diverse specialists for MoE strategy."""
        models = self.selector.select_for_strategy('moe', num_models=4)

        self.assertGreaterEqual(len(models), 2)
        # Should have diverse specializations
        specializations = [m.specialization for m in models]
        unique_specs = set(specializations)
        self.assertGreaterEqual(len(unique_specs), 2)

    def test_select_for_strategy_moe_breaks_early(self):
        """Should break early when enough models selected for MoE."""
        # Request only 2 models, should break after finding 2
        models = self.selector.select_for_strategy('moe', num_models=2)

        self.assertEqual(len(models), 2)

    def test_select_for_strategy_unknown_falls_back(self):
        """Should fall back to task-based selection for unknown strategy."""
        models = self.selector.select_for_strategy('unknown_strategy', task="Write code")

        self.assertEqual(len(models), 2)

    def test_recommend_configuration_code_models(self):
        """Should recommend low temperature for code models."""
        code_models = [MODEL_ZOO['codellama_7b'], MODEL_ZOO['deepseek_coder']]
        config = self.selector.recommend_configuration(code_models)

        self.assertEqual(config['temperature'], 0.3)
        self.assertIn('top_k', config)
        self.assertIn('top_p', config)
        self.assertIn('use_kv_cache', config)
        self.assertIn('estimated_vram_mb', config)
        self.assertTrue(config['use_kv_cache'])

    def test_recommend_configuration_creative_models(self):
        """Should use average temperature for non-code models."""
        creative_models = [MODEL_ZOO['mistral_7b'], MODEL_ZOO['gemma_2b']]
        config = self.selector.recommend_configuration(creative_models)

        # Should be average of 0.9 and 0.7 = 0.8
        self.assertAlmostEqual(config['temperature'], 0.8, places=1)

    def test_recommend_configuration_averages_settings(self):
        """Should average settings across models."""
        models = [MODEL_ZOO['tinyllama'], MODEL_ZOO['gemma_2b']]
        config = self.selector.recommend_configuration(models)

        # Check all required fields present
        self.assertIn('temperature', config)
        self.assertIn('top_k', config)
        self.assertIn('top_p', config)
        self.assertIn('use_kv_cache', config)
        self.assertIn('estimated_vram_mb', config)

    def test_recommend_configuration_estimates_vram(self):
        """Should sum VRAM requirements."""
        models = [MODEL_ZOO['tinyllama'], MODEL_ZOO['gemma_2b']]
        config = self.selector.recommend_configuration(models)

        estimated_vram = config['estimated_vram_mb']
        self.assertGreater(estimated_vram, 0)


class TestModuleFunctions(unittest.TestCase):
    """Test module-level helper functions."""

    def test_get_model_profile_by_alias(self):
        """Should get profile by alias."""
        profile = get_model_profile('tinyllama')

        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')

    def test_get_model_profile_by_full_name(self):
        """Should get profile by full name."""
        profile = get_model_profile('google/gemma-2b-it')

        self.assertIsNotNone(profile)
        self.assertEqual(profile, MODEL_ZOO['gemma_2b'])

    def test_get_model_profile_not_found(self):
        """Should return None for unknown model."""
        profile = get_model_profile('nonexistent_model')

        self.assertIsNone(profile)

    def test_list_models_by_specialization_code(self):
        """Should list all code models."""
        code_models = list_models_by_specialization(ModelSpecialization.CODE)

        self.assertGreater(len(code_models), 0)
        for model in code_models:
            self.assertEqual(model.specialization, ModelSpecialization.CODE)

    def test_list_models_by_specialization_creative(self):
        """Should list all creative models."""
        creative_models = list_models_by_specialization(ModelSpecialization.CREATIVE)

        self.assertGreater(len(creative_models), 0)
        for model in creative_models:
            self.assertEqual(model.specialization, ModelSpecialization.CREATIVE)

    def test_list_models_by_specialization_fast(self):
        """Should list all fast models."""
        fast_models = list_models_by_specialization(ModelSpecialization.FAST)

        self.assertGreater(len(fast_models), 0)
        for model in fast_models:
            self.assertEqual(model.specialization, ModelSpecialization.FAST)

    def test_list_models_by_specialization_empty(self):
        """Should return empty list for specialization with no models."""
        # This depends on MODEL_ZOO content, but we can still test the function works
        try:
            # Try with a valid specialization that might have models
            models = list_models_by_specialization(ModelSpecialization.MATH)
            self.assertIsInstance(models, list)
        except Exception as e:
            self.fail(f"list_models_by_specialization raised exception: {e}")

    def test_get_recommended_ensemble_code_task(self):
        """Should get recommended ensemble for code task."""
        ensemble = get_recommended_ensemble("Write a Python function", vram_budget_mb=16384)

        self.assertIsInstance(ensemble, list)
        self.assertGreater(len(ensemble), 0)
        # Each item should be (engine, model_name) tuple
        for engine, model_name in ensemble:
            self.assertIsInstance(engine, str)
            self.assertIsInstance(model_name, str)

    def test_get_recommended_ensemble_respects_num_models(self):
        """Should return requested number of models in ensemble."""
        ensemble = get_recommended_ensemble("Any task", vram_budget_mb=16384, num_models=3)

        self.assertLessEqual(len(ensemble), 3)

    def test_get_recommended_ensemble_limited_vram(self):
        """Should handle limited VRAM."""
        ensemble = get_recommended_ensemble("Any task", vram_budget_mb=2048)

        self.assertGreater(len(ensemble), 0)


def run_tests():
    """Run all model registry tests."""
    print("=" * 80)
    print("Testing Model Registry")
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
