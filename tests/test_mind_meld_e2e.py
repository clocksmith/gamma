#!/usr/bin/env python3
"""
End-to-end test for GAMMA Mind Meld implementation.

Tests all new features:
- Model Registry
- Swap Strategies
- Advanced Features (Speculative, Contrastive, MoE, etc.)
- Infrastructure (Cache, Async, Streaming)
- Benchmarking
- Presets
"""

import sys
import time
import numpy as np
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock, Mock

sys.path.insert(0, 'src')

# Import all new components
from src.core.model_registry import ModelSelector, ModelProfile, ModelSpecialization, get_recommended_ensemble, MODEL_ZOO
from src.mind_meld.strategies.base_strategy import (
    SwapStrategyBase, SwapDecision,
    FixedIntervalStrategy, PatternBasedStrategy, RoundRobinStrategy, RandomStrategy
)
from src.mind_meld.strategies.perplexity_strategy import PerplexitySwapStrategy, ConfidenceBasedStrategy
from src.mind_meld.strategies.semantic_strategy import SemanticSimilarityStrategy, SyntacticRoleStrategy
from src.mind_meld.advanced.speculative_decoding import SpeculativeDecoder, SpeculativeMeldEngine
from src.mind_meld.advanced.contrastive_decoding import ContrastiveDecoder, ContrastiveConfig
from src.mind_meld.advanced.moe_router import ContentType, ContentClassifier, MoERouter, AdaptiveMoERouter
from src.mind_meld.advanced.feedback_loop import FeedbackLoop, FeedbackType, FeedbackResult
from src.mind_meld.advanced.hierarchical_control import HierarchicalController, PlanStep, ExecutionPlan
from src.mind_meld.advanced.adversarial import AdversarialDebate, Claim, Challenge, DebateResult
from src.benchmarks.mind_meld_benchmark import MindMeldBenchmark, BenchmarkConfig, BenchmarkResult
from src.infrastructure.cache_manager import KVCacheCompressor, ModelCache, AsyncModelLoader, StreamingGenerator
from src.mind_meld.presets import (
    PresetType, MeldPreset, get_preset, list_presets,
    get_preset_by_name, get_recommended_preset, create_custom_preset
)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")

    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")

    def print_summary(self):
        total = self.passed + self.failed
        print("\n" + "="*70)
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print("="*70)


def create_mock_engine(name: str = "test_model") -> MagicMock:
    """Create a mock LLM engine for testing."""
    engine = MagicMock()
    engine.model_name = name
    engine.get_vocabulary_size.return_value = 32000
    engine.get_eos_token_id.return_value = 2
    engine.get_token_text = lambda tid: f"token_{tid}"
    engine.tokenizer = MagicMock()
    engine.tokenizer.eos_token_id = 2
    engine.convert_to_numpy = lambda x: np.array(x) if not isinstance(x, np.ndarray) else x

    # Mock encode to return numpy arrays
    def mock_encode(text, add_special_tokens=True):
        tokens = np.array([[1, 2, 3, 4, 5]])
        mask = np.ones_like(tokens)
        return tokens, mask

    engine.encode = mock_encode

    # Mock predict_next (accept all args including positional and keyword)
    def mock_predict_next(*args, **kwargs):
        vocab_size = 32000
        logits = np.random.randn(vocab_size).astype(np.float32)
        return {
            'logits': logits,
            'logits_raw': logits,  # For contrastive decoding
            'next_token_id': 100,
            'next_token_text': 'test'
        }

    engine.predict_next = mock_predict_next
    engine.decode = lambda ids, **kwargs: "generated text"

    return engine


# ============================================================================
# TEST SUITES
# ============================================================================

def test_model_registry(results: TestResults):
    """Test Model Registry & Auto-Selection."""
    print("\n" + "="*70)
    print("Testing Model Registry & Auto-Selection")
    print("="*70)

    try:
        # Test MODEL_ZOO access
        assert len(MODEL_ZOO) > 0
        assert 'gemma_2_2b' in MODEL_ZOO
        results.record_pass("MODEL_ZOO access")
    except Exception as e:
        results.record_fail("MODEL_ZOO access", str(e))
        return

    try:
        # Test getting model by name
        profile = MODEL_ZOO.get('gemma_2_2b')
        assert profile is not None
        assert isinstance(profile.specialization, ModelSpecialization)
        results.record_pass("Get model by name")
    except Exception as e:
        results.record_fail("Get model by name", str(e))

    try:
        # Test model selector
        selector = ModelSelector(available_vram_mb=16384)
        models = selector.select_for_task("Write Python code", num_models=2)
        assert len(models) <= 2
        results.record_pass("Task-based model selection")
    except Exception as e:
        results.record_fail("Task-based model selection", str(e))

    try:
        # Test strategy-based selection
        models = selector.select_for_strategy('moe', task="general", num_models=3)
        assert len(models) <= 3
        results.record_pass("Strategy-based model selection")
    except Exception as e:
        results.record_fail("Strategy-based model selection", str(e))

    try:
        # Test recommended ensemble
        ensemble = get_recommended_ensemble("Write creative story", 8192, 2)
        assert len(ensemble) <= 2
        results.record_pass("Get recommended ensemble")
    except Exception as e:
        results.record_fail("Get recommended ensemble", str(e))


def test_swap_strategies(results: TestResults):
    """Test all swap strategies."""
    print("\n" + "="*70)
    print("Testing Swap Strategies")
    print("="*70)

    # Test data
    logits = np.random.randn(32000).astype(np.float32)
    context = "The quick brown fox"

    try:
        # Fixed Interval Strategy
        strategy = FixedIntervalStrategy(interval=5)
        for i in range(7):
            decision = strategy.should_swap("test", logits, 0, 2, context)
            if i == 4:  # Should swap on 5th call (0-indexed)
                assert decision.should_swap
        results.record_pass("FixedIntervalStrategy")
    except Exception as e:
        results.record_fail("FixedIntervalStrategy", str(e))

    try:
        # Pattern Based Strategy
        strategy = PatternBasedStrategy(patterns=['.', '!', '?'])
        decision = strategy.should_swap(".", logits, 0, 2, context)
        assert decision.should_swap
        results.record_pass("PatternBasedStrategy")
    except Exception as e:
        results.record_fail("PatternBasedStrategy", str(e))

    try:
        # Round Robin Strategy
        strategy = RoundRobinStrategy()
        decision = strategy.should_swap("test", logits, 0, 3, context)
        assert decision.should_swap
        results.record_pass("RoundRobinStrategy")
    except Exception as e:
        results.record_fail("RoundRobinStrategy", str(e))

    try:
        # Random Strategy
        strategy = RandomStrategy(probability=0.5)
        decision = strategy.should_swap("test", logits, 0, 2, context)
        results.record_pass("RandomStrategy")
    except Exception as e:
        results.record_fail("RandomStrategy", str(e))

    try:
        # Perplexity Strategy
        strategy = PerplexitySwapStrategy(threshold=50.0, adaptive=True)
        decision = strategy.should_swap("test", logits, 0, 2, context, token_id=100)
        results.record_pass("PerplexitySwapStrategy")
    except Exception as e:
        results.record_fail("PerplexitySwapStrategy", str(e))

    try:
        # Confidence Based Strategy
        strategy = ConfidenceBasedStrategy(min_confidence=0.7)
        decision = strategy.should_swap("test", logits, 0, 2, context, token_id=100)
        results.record_pass("ConfidenceBasedStrategy")
    except Exception as e:
        results.record_fail("ConfidenceBasedStrategy", str(e))

    try:
        # Semantic Similarity Strategy (without embeddings)
        strategy = SemanticSimilarityStrategy(
            similarity_threshold=0.7,
            use_embeddings=False  # Use word overlap fallback
        )
        decision = strategy.should_swap("test", logits, 0, 2, "Different context entirely")
        results.record_pass("SemanticSimilarityStrategy (word overlap)")
    except Exception as e:
        results.record_fail("SemanticSimilarityStrategy", str(e))


def test_speculative_decoding(results: TestResults):
    """Test Speculative Decoding."""
    print("\n" + "="*70)
    print("Testing Speculative Decoding")
    print("="*70)

    try:
        draft_model = create_mock_engine("draft")
        target_model = create_mock_engine("target")

        decoder = SpeculativeDecoder(
            draft_model=draft_model,
            target_model=target_model,
            k=4,
            verbose=False
        )
        results.record_pass("SpeculativeDecoder initialization")
    except Exception as e:
        results.record_fail("SpeculativeDecoder initialization", str(e))
        return

    try:
        # Test generation step
        context = "Test context"
        from src.mind_meld.advanced.speculative_decoding import SpeculativeResult
        result = decoder.generate_step(context)
        assert isinstance(result, SpeculativeResult)
        assert result.num_accepted >= 0
        results.record_pass("SpeculativeDecoder generation step")
    except Exception as e:
        results.record_fail("SpeculativeDecoder generation step", str(e))

    try:
        # Test full generation
        generated, stats = decoder.generate("Test prompt", max_tokens=10)
        assert isinstance(generated, str)
        assert 'total_tokens' in stats
        assert 'tokens_per_second' in stats
        results.record_pass("SpeculativeDecoder full generation")
    except Exception as e:
        results.record_fail("SpeculativeDecoder full generation", str(e))


def test_contrastive_decoding(results: TestResults):
    """Test Contrastive Decoding."""
    print("\n" + "="*70)
    print("Testing Contrastive Decoding")
    print("="*70)

    try:
        expert = create_mock_engine("expert")
        amateur = create_mock_engine("amateur")

        config = ContrastiveConfig(alpha=0.5, use_adaptive_alpha=True)
        decoder = ContrastiveDecoder(expert, amateur, config, verbose=False)
        results.record_pass("ContrastiveDecoder initialization")
    except Exception as e:
        results.record_fail("ContrastiveDecoder initialization", str(e))
        return

    try:
        # Test logit contrasting
        expert_logits = np.random.randn(32000).astype(np.float32)
        amateur_logits = np.random.randn(32000).astype(np.float32)
        contrasted = decoder.contrast_logits(expert_logits, amateur_logits)
        assert contrasted.shape == expert_logits.shape
        results.record_pass("ContrastiveDecoder logit contrasting")
    except Exception as e:
        results.record_fail("ContrastiveDecoder logit contrasting", str(e))

    try:
        # Test generation
        generated, stats = decoder.generate("Test prompt", max_tokens=10)
        assert isinstance(generated, str)
        assert 'agreement_rate' in stats
        results.record_pass("ContrastiveDecoder generation")
    except Exception as e:
        results.record_fail("ContrastiveDecoder generation", str(e))


def test_moe_router(results: TestResults):
    """Test MoE-Style Routing."""
    print("\n" + "="*70)
    print("Testing MoE-Style Routing")
    print("="*70)

    try:
        # Test content classifier
        classifier = ContentClassifier()
        content_type = classifier.classify_context("def factorial(n): return 1 if n <= 1 else n * factorial(n-1)")
        assert content_type == ContentType.CODE
        results.record_pass("ContentClassifier code detection")
    except Exception as e:
        results.record_fail("ContentClassifier", str(e))

    try:
        # Test MoE Router
        models = {
            ContentType.CODE: create_mock_engine("code_model"),
            ContentType.PROSE: create_mock_engine("prose_model"),
            ContentType.TECHNICAL: create_mock_engine("tech_model"),
        }

        router = MoERouter(models, verbose=False)
        results.record_pass("MoERouter initialization")
    except Exception as e:
        results.record_fail("MoERouter initialization", str(e))
        return

    try:
        # Test routing
        generated, stats = router.generate("Write a Python function", max_tokens=10)
        assert isinstance(generated, str)
        assert 'content_distribution' in stats
        results.record_pass("MoERouter generation")
    except Exception as e:
        results.record_fail("MoERouter generation", str(e))


def test_feedback_loop(results: TestResults):
    """Test Feedback Loop System."""
    print("\n" + "="*70)
    print("Testing Feedback Loop System")
    print("="*70)

    try:
        generator = create_mock_engine("generator")
        critic = create_mock_engine("critic")

        loop = FeedbackLoop(
            generator_model=generator,
            critic_model=critic,
            max_iterations=2,
            min_score_threshold=0.8,
            verbose=False
        )
        results.record_pass("FeedbackLoop initialization")
    except Exception as e:
        results.record_fail("FeedbackLoop initialization", str(e))
        return

    try:
        # Test feedback loop run
        result = loop.run_loop(
            prompt="Write a paragraph",
            max_tokens=20,
            aspects=[FeedbackType.GRAMMAR, FeedbackType.COHERENCE]
        )
        assert isinstance(result, FeedbackResult)
        assert result.original_text is not None
        results.record_pass("FeedbackLoop run")
    except Exception as e:
        results.record_fail("FeedbackLoop run", str(e))


def test_hierarchical_control(results: TestResults):
    """Test Hierarchical Control."""
    print("\n" + "="*70)
    print("Testing Hierarchical Control")
    print("="*70)

    try:
        meta = create_mock_engine("meta")
        specialists = {
            PlanStep.INTRODUCE: create_mock_engine("intro"),
            PlanStep.EXPLAIN: create_mock_engine("explain"),
        }

        controller = HierarchicalController(meta, specialists, verbose=False)
        results.record_pass("HierarchicalController initialization")
    except Exception as e:
        results.record_fail("HierarchicalController initialization", str(e))
        return

    try:
        # Test planning and generation
        generated, plan = controller.generate_with_planning(
            objective="Explain binary search",
            max_steps=3
        )
        assert isinstance(generated, str)
        assert isinstance(plan, ExecutionPlan)
        results.record_pass("HierarchicalController generation")
    except Exception as e:
        results.record_fail("HierarchicalController generation", str(e))


def test_adversarial_debate(results: TestResults):
    """Test Adversarial Debate."""
    print("\n" + "="*70)
    print("Testing Adversarial Debate")
    print("="*70)

    try:
        red_team = create_mock_engine("red")
        blue_team = create_mock_engine("blue")

        debate = AdversarialDebate(
            red_team=red_team,
            blue_team=blue_team,
            max_rounds=2,
            verbose=False
        )
        results.record_pass("AdversarialDebate initialization")
    except Exception as e:
        results.record_fail("AdversarialDebate initialization", str(e))
        return

    try:
        # Test debate
        consensus, result = debate.generate_with_debate("Climate change impacts")
        assert isinstance(consensus, str)
        assert isinstance(result, DebateResult)
        results.record_pass("AdversarialDebate generation")
    except Exception as e:
        results.record_fail("AdversarialDebate generation", str(e))


def test_infrastructure(results: TestResults):
    """Test Infrastructure Components."""
    print("\n" + "="*70)
    print("Testing Infrastructure (Cache, Async, Streaming)")
    print("="*70)

    try:
        # Test KV Cache Compressor
        compressor = KVCacheCompressor(compression_ratio=0.5, quantization_bits=8)
        cache = np.random.randn(1, 12, 128, 64).astype(np.float32)
        compressed, metadata = compressor.compress_cache(cache, layer_idx=0)
        assert compressed.nbytes < cache.nbytes
        results.record_pass("KVCacheCompressor")
    except Exception as e:
        results.record_fail("KVCacheCompressor", str(e))

    try:
        # Test Model Cache
        cache = ModelCache(max_vram_mb=16384, verbose=False)
        stats = cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        results.record_pass("ModelCache")
    except Exception as e:
        results.record_fail("ModelCache", str(e))

    try:
        # Test Streaming Generator (just initialization)
        engine = create_mock_engine()
        generator = StreamingGenerator(engine)
        results.record_pass("StreamingGenerator initialization")
    except Exception as e:
        results.record_fail("StreamingGenerator", str(e))


def test_benchmarking(results: TestResults):
    """Test Benchmarking Suite."""
    print("\n" + "="*70)
    print("Testing Benchmarking Suite")
    print("="*70)

    try:
        benchmark = MindMeldBenchmark(verbose=False)
        results.record_pass("MindMeldBenchmark initialization")
    except Exception as e:
        results.record_fail("MindMeldBenchmark initialization", str(e))
        return

    try:
        # Test config creation
        config = BenchmarkConfig(
            strategy_name="perplexity",
            models=['model1', 'model2'],
            prompt="Test prompt",
            max_tokens=50
        )
        assert config.strategy_name == "perplexity"
        results.record_pass("BenchmarkConfig creation")
    except Exception as e:
        results.record_fail("BenchmarkConfig creation", str(e))


def test_presets(results: TestResults):
    """Test Configuration Presets."""
    print("\n" + "="*70)
    print("Testing Configuration Presets")
    print("="*70)

    try:
        # Test getting preset
        preset = get_preset(PresetType.CODE_GENERATION)
        assert preset.name == "Code Generation"
        assert preset.use_abe == True
        results.record_pass("Get preset")
    except Exception as e:
        results.record_fail("Get preset", str(e))

    try:
        # Test listing presets
        presets = list_presets()
        assert len(presets) == 8
        results.record_pass("List presets")
    except Exception as e:
        results.record_fail("List presets", str(e))

    try:
        # Test preset by name
        preset = get_preset_by_name("creative_writing")
        assert preset is not None
        results.record_pass("Get preset by name")
    except Exception as e:
        results.record_fail("Get preset by name", str(e))

    try:
        # Test recommended preset
        preset = get_recommended_preset("Write code for sorting")
        assert preset.name == "Code Generation"
        results.record_pass("Get recommended preset")
    except Exception as e:
        results.record_fail("Get recommended preset", str(e))

    try:
        # Test custom preset creation
        custom = create_custom_preset(
            name="My Custom",
            models=['model1', 'model2'],
            strategy='fixed',
            temperature=0.8
        )
        assert custom.name == "My Custom"
        assert custom.temperature == 0.8
        results.record_pass("Create custom preset")
    except Exception as e:
        results.record_fail("Create custom preset", str(e))


def test_integration(results: TestResults):
    """Test component integration."""
    print("\n" + "="*70)
    print("Testing Component Integration")
    print("="*70)

    try:
        # Test combining preset with strategies
        preset = get_preset(PresetType.FAST_GENERATION)

        # Create strategy from preset
        if preset.strategy == 'fixed':
            strategy = FixedIntervalStrategy(
                interval=preset.additional_config.get('fixed_interval', 5)
            )

        # Test strategy with mock data
        logits = np.random.randn(32000).astype(np.float32)
        decision = strategy.should_swap("test", logits, 0, 2, "context")

        results.record_pass("Preset + Strategy integration")
    except Exception as e:
        results.record_fail("Preset + Strategy integration", str(e))

    try:
        # Test model selector with preset
        preset = get_preset(PresetType.CODE_GENERATION)
        selector = ModelSelector(available_vram_mb=16384)

        # Try to find models for the preset
        models = selector.select_for_task("code generation", num_models=2)

        results.record_pass("Model Selector + Preset integration")
    except Exception as e:
        results.record_fail("Model Selector + Preset integration", str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  GAMMA Mind Meld - End-to-End Test Suite")
    print("="*70)
    print("\nTesting all new features:")
    print("  - Model Registry & Auto-Selection")
    print("  - Swap Strategies (6 types)")
    print("  - Advanced Features (7 techniques)")
    print("  - Infrastructure (Cache, Async, Streaming)")
    print("  - Benchmarking Suite")
    print("  - Configuration Presets (8 types)")
    print("  - Component Integration")

    results = TestResults()
    start_time = time.time()

    # Run all test suites
    test_model_registry(results)
    test_swap_strategies(results)
    test_speculative_decoding(results)
    test_contrastive_decoding(results)
    test_moe_router(results)
    test_feedback_loop(results)
    test_hierarchical_control(results)
    test_adversarial_debate(results)
    test_infrastructure(results)
    test_benchmarking(results)
    test_presets(results)
    test_integration(results)

    elapsed = time.time() - start_time

    # Print summary
    results.print_summary()
    print(f"\nTotal time: {elapsed:.2f}s")

    if results.failed == 0:
        print("\n✅ ALL TESTS PASSED! Implementation is working correctly.")
        return 0
    else:
        print(f"\n❌ {results.failed} tests failed. See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
