#!/usr/bin/env python3
"""
Example: Integrating new Mind Meld features with GAMMA

This script demonstrates how to use the new Mind Meld features
in a practical scenario.
"""

import sys
sys.path.insert(0, 'src')

from src.core.model_registry import ModelSelector, get_recommended_ensemble, MODEL_ZOO
from src.mind_meld.strategies.perplexity_strategy import PerplexitySwapStrategy
from src.mind_meld.strategies.semantic_strategy import SemanticSimilarityStrategy
from src.mind_meld.presets import get_preset, PresetType, get_recommended_preset
from src.infrastructure.cache_manager import ModelCache


def example_1_preset_based():
    """Example 1: Using presets for quick setup."""
    print("\n" + "="*70)
    print("Example 1: Using Presets for Quick Setup")
    print("="*70)

    # Get preset for code generation
    preset = get_preset(PresetType.CODE_GENERATION)

    print(f"\n✓ Preset: {preset.name}")
    print(f"  Description: {preset.description}")
    print(f"  Models: {preset.models}")
    print(f"  Strategy: {preset.strategy}")
    print(f"  Temperature: {preset.temperature}")
    print(f"  Features enabled:")
    print(f"    - ABE (Agreement-Based Ensembling): {preset.use_abe}")
    print(f"    - MoE (Mixture of Experts): {preset.use_moe}")
    print(f"    - Feedback Loop: {preset.use_feedback}")

    # Or get recommended preset from task description
    recommended = get_recommended_preset("Write a creative story about space")
    print(f"\n✓ Recommended for creative writing: {recommended.name}")


def example_2_model_selection():
    """Example 2: Intelligent model selection based on hardware."""
    print("\n" + "="*70)
    print("Example 2: Hardware-Aware Model Selection")
    print("="*70)

    # Initialize selector with your VRAM budget
    selector = ModelSelector(available_vram_mb=16384)  # 16GB VRAM

    # Select models for a task
    models = selector.select_for_task(
        "Write a Python function to sort a list",
        num_models=2
    )

    print(f"\n✓ Selected {len(models)} models:")
    for i, model in enumerate(models, 1):
        print(f"\n  {i}. {model.name}")
        print(f"     Engine: {model.engine}")
        print(f"     Specialization: {model.specialization.value}")
        print(f"     VRAM required: {model.min_vram_mb}MB")
        print(f"     Strengths: {', '.join(model.strengths[:3])}")

    # Select models for MoE strategy
    moe_models = selector.select_for_strategy('moe', task="mixed content", num_models=4)
    print(f"\n✓ Selected {len(moe_models)} diverse models for MoE routing")


def example_3_swap_strategies():
    """Example 3: Comparing swap strategies."""
    print("\n" + "="*70)
    print("Example 3: Swap Strategy Configuration")
    print("="*70)

    # Perplexity-based: swap when model is uncertain
    perplexity_strategy = PerplexitySwapStrategy(
        threshold=50.0,       # Swap when perplexity > 50
        adaptive=True,        # Auto-adjust threshold
        window_size=3,        # Smooth over 3 tokens
        verbose=False
    )
    print("\n✓ Perplexity Strategy configured")
    print(f"  Threshold: 50.0 (adaptive)")
    print(f"  Use case: Swap when model is uncertain")

    # Semantic similarity: swap on context drift
    semantic_strategy = SemanticSimilarityStrategy(
        similarity_threshold=0.7,
        use_embeddings=False,  # Use word overlap fallback
        window_size=50,
        verbose=False
    )
    print("\n✓ Semantic Strategy configured")
    print(f"  Threshold: 0.7 similarity")
    print(f"  Use case: Swap when context changes significantly")


def example_4_model_cache():
    """Example 4: Using model cache for VRAM management."""
    print("\n" + "="*70)
    print("Example 4: Model Cache for VRAM Management")
    print("="*70)

    # Create cache with VRAM budget
    cache = ModelCache(max_vram_mb=16384, verbose=False)

    print("\n✓ Model Cache initialized")
    print(f"  Max VRAM: {cache.max_vram_mb}MB")
    print(f"  Current usage: {cache.get_current_usage()}MB")

    # Get stats
    stats = cache.get_stats()
    print(f"\n  Statistics:")
    print(f"    - Cache hits: {stats['hits']}")
    print(f"    - Cache misses: {stats['misses']}")
    print(f"    - Evictions: {stats['evictions']}")
    print(f"    - Hit rate: {stats['hit_rate']:.1%}")


def example_5_model_zoo():
    """Example 5: Exploring the model zoo."""
    print("\n" + "="*70)
    print("Example 5: Exploring Available Models")
    print("="*70)

    print(f"\n✓ Total models available: {len(MODEL_ZOO)}")

    # Show models by specialization
    from src.core.model_registry import ModelSpecialization

    for spec in ModelSpecialization:
        models = [name for name, profile in MODEL_ZOO.items()
                 if profile.specialization == spec]
        if models:
            print(f"\n  {spec.value.upper()}: {len(models)} models")
            for model_name in models[:3]:  # Show first 3
                profile = MODEL_ZOO[model_name]
                print(f"    - {profile.name} ({profile.size_mb}MB)")


def example_6_integration_with_game():
    """Example 6: How to integrate with game.py."""
    print("\n" + "="*70)
    print("Example 6: Integration with GAMMA Game")
    print("="*70)

    print("""
To use new features with game.py:

1. Using presets in Mind Meld mode:

   python game.py --mind-meld \\
       --meld-models "TinyLlama/TinyLlama-1.1B-Chat-v1.0" "Qwen/Qwen2-1.5B-Instruct" \\
       --swap-strategy perplexity \\
       --use-abe \\
       --steps 100

2. Using model selector programmatically:

   from src.core.model_registry import ModelSelector
   selector = ModelSelector(available_vram_mb=16384)
   models = selector.select_for_task("your task", num_models=2)
   # Use models[0].name and models[1].name as --meld-models

3. Using presets:

   from src.mind_meld.presets import get_preset, PresetType
   preset = get_preset(PresetType.CODE_GENERATION)
   # Apply preset settings to your args
   args.temperature = preset.temperature
   args.use_abe = preset.use_abe
   args.swap_strategy = preset.strategy

4. Running benchmarks:

   from src.benchmarks.mind_meld_benchmark import MindMeldBenchmark
   benchmark = MindMeldBenchmark()
   # Configure and run benchmarks on your setup
    """)


def example_7_complete_workflow():
    """Example 7: Complete workflow from task to configuration."""
    print("\n" + "="*70)
    print("Example 7: Complete Workflow")
    print("="*70)

    task = "Write technical documentation with code examples"
    vram_budget = 16384

    print(f"\nTask: {task}")
    print(f"Available VRAM: {vram_budget}MB")

    # Step 1: Get recommended preset
    preset = get_recommended_preset(task)
    print(f"\n1. Recommended preset: {preset.name}")

    # Step 2: Select models
    selector = ModelSelector(available_vram_mb=vram_budget)
    models = selector.select_for_task(task, num_models=2)
    print(f"\n2. Selected models:")
    for model in models:
        print(f"   - {model.name} ({model.specialization.value})")

    # Step 3: Configure strategy
    print(f"\n3. Swap strategy: {preset.strategy}")
    print(f"   - Temperature: {preset.temperature}")
    print(f"   - Top-K: {preset.top_k}")
    print(f"   - Top-P: {preset.top_p}")

    # Step 4: Enable features
    print(f"\n4. Advanced features:")
    features = []
    if preset.use_abe: features.append("Agreement-Based Ensembling")
    if preset.use_moe: features.append("MoE Routing")
    if preset.use_feedback: features.append("Feedback Loop")
    if preset.use_hierarchical: features.append("Hierarchical Control")
    if preset.use_adversarial: features.append("Adversarial Debate")

    for feature in features:
        print(f"   ✓ {feature}")

    print("\n✅ Ready to run Mind Meld with optimal configuration!")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("  GAMMA Mind Meld - Integration Examples")
    print("="*70)
    print("\nDemonstrating how to use new features in practice...")

    try:
        example_1_preset_based()
        example_2_model_selection()
        example_3_swap_strategies()
        example_4_model_cache()
        example_5_model_zoo()
        example_6_integration_with_game()
        example_7_complete_workflow()

        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Run actual models: python game.py --mind-meld --meld-models ...")
        print("  2. Test benchmarks: See MIND_MELD_GUIDE.md")
        print("  3. Customize presets: See src/mind_meld/presets.py")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
