# GAMMA Mind Meld - Complete Guide

## 🚀 New Features Implemented

### **1. Model Registry & Auto-Selection**
Intelligent model selection based on task and hardware capabilities.

```python
from src.core.model_registry import ModelSelector, get_recommended_ensemble

# Auto-select models for your hardware
selector = ModelSelector(available_vram_mb=16384)  # 16GB VRAM

# Get models for a specific task
models = selector.select_for_task(
    "Write a Python function to parse JSON",
    num_models=2
)

print(f"Selected: {[m.name for m in models]}")
# Output: ['codellama/CodeLlama-7b-Instruct-hf', 'google/gemma-2-9b-it']

# Or use quick helper
ensemble = get_recommended_ensemble(
    task="Write a creative story",
    vram_budget_mb=12288,
    num_models=2
)
```

### **2. Advanced Swap Strategies**

#### **Perplexity-Based** (Swap when model is uncertain)
```python
from src.mind_meld.strategies.perplexity_strategy import PerplexitySwapStrategy

strategy = PerplexitySwapStrategy(
    threshold=50.0,  # Swap when perplexity > 50
    adaptive=True,   # Auto-adjust threshold
    verbose=True
)

# Use in meld engine
decision = strategy.should_swap(
    token_text="quantum",
    logits=model_logits,
    current_model_idx=0,
    num_models=2
)

if decision.should_swap:
    print(f"Swapping: {decision.reason}")
```

#### **Semantic Similarity** (Swap on context drift)
```python
from src.mind_meld.strategies.semantic_strategy import SemanticSimilarityStrategy

strategy = SemanticSimilarityStrategy(
    similarity_threshold=0.7,
    use_embeddings=True,  # Uses sentence-transformers
    verbose=True
)
```

### **3. Speculative Decoding** (2-3x Speedup!)

```python
from src.mind_meld.advanced.speculative_decoding import SpeculativeDecoder

# Setup: fast draft model + slow target model
draft_model = get_engine('pytorch', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
target_model = get_engine('pytorch', 'google/gemma-2-9b-it')

decoder = SpeculativeDecoder(
    draft_model=draft_model,
    target_model=target_model,
    k=4,  # Speculate 4 tokens ahead
    verbose=True
)

# Generate with 2-3x speedup
generated, stats = decoder.generate(
    prompt="Explain quantum computing",
    max_tokens=100
)

print(f"Speed: {stats['tokens_per_second']:.2f} tok/s")
print(f"Acceptance rate: {stats['acceptance_rate']:.1%}")
```

### **4. Contrastive Decoding** (Amplify Expert Capabilities)

```python
from src.mind_meld.advanced.contrastive_decoding import ContrastiveDecoder, ContrastiveConfig

# Setup: large expert + small amateur
expert = get_engine('pytorch', 'google/gemma-2-9b-it')
amateur = get_engine('pytorch', 'google/gemma-2b-it')

config = ContrastiveConfig(
    alpha=0.5,  # Contrast weight
    use_adaptive_alpha=True  # Adapt based on disagreement
)

decoder = ContrastiveDecoder(expert, amateur, config, verbose=True)

generated, stats = decoder.generate(
    prompt="Write a technical explanation of neural networks",
    max_tokens=150
)

print(f"Agreement rate: {stats['agreement_rate']:.1%}")
```

### **5. MoE-Style Content Routing**

```python
from src.mind_meld.advanced.moe_router import MoERouter, ContentType

# Setup specialists
models = {
    ContentType.CODE: get_engine('pytorch', 'codellama/CodeLlama-7b-Instruct-hf'),
    ContentType.PROSE: get_engine('pytorch', 'google/gemma-2-2b-it'),
    ContentType.MATH: get_engine('pytorch', 'mistralai/mathstral-7B-v0.1'),
    ContentType.CREATIVE: get_engine('pytorch', 'mistralai/Mistral-7B-Instruct-v0.2')
}

router = MoERouter(models, verbose=True)

generated, stats = router.generate(
    prompt="Explain recursion with a Python example",
    max_tokens=200
)

print(f"Content distribution: {stats['content_distribution']}")
print(f"Model switches: {stats['model_switches']}")
```

### **6. Feedback Loop System** (Self-Critique)

```python
from src.mind_meld.advanced.feedback_loop import FeedbackLoop, FeedbackType

generator = get_engine('pytorch', 'google/gemma-2-9b-it')
critic = get_engine('pytorch', 'google/gemma-2-9b-it')  # Can be same model

loop = FeedbackLoop(
    generator_model=generator,
    critic_model=critic,
    max_iterations=3,
    min_score_threshold=0.8
)

result = loop.run_loop(
    prompt="Write a paragraph about climate change",
    max_tokens=100,
    aspects=[FeedbackType.GRAMMAR, FeedbackType.COHERENCE, FeedbackType.FACTUALITY]
)

print(f"Original: {result.original_text}")
print(f"Revised: {result.revised_text}")
print(f"Iterations: {result.num_iterations}")
print(f"Improvement: {result.improvement_score:.3f}")
```

### **7. Hierarchical Control** (Meta-Planning)

```python
from src.mind_meld.advanced.hierarchical_control import HierarchicalController, PlanStep

meta_model = get_engine('pytorch', 'google/gemma-2-9b-it')
specialists = {
    PlanStep.CODE_EXAMPLE: get_engine('pytorch', 'codellama/CodeLlama-7b-Instruct-hf'),
    PlanStep.EXPLAIN: get_engine('pytorch', 'google/gemma-7b-it'),
    PlanStep.CONCLUDE: get_engine('pytorch', 'mistralai/Mistral-7B-Instruct-v0.2')
}

controller = HierarchicalController(meta_model, specialists, verbose=True)

generated, plan = controller.generate_with_planning(
    objective="Explain binary search with code example",
    max_steps=5
)

print(f"Generated with {len(plan.steps)} steps:")
for step_type, desc in plan.steps:
    print(f"  - {step_type.value}: {desc}")
```

### **8. Adversarial Dynamics** (Red vs Blue Team)

```python
from src.mind_meld.advanced.adversarial import AdversarialDebate

red_team = get_engine('pytorch', 'google/gemma-2-9b-it')
blue_team = get_engine('pytorch', 'google/gemma-2-9b-it')

debate = AdversarialDebate(
    red_team=red_team,
    blue_team=blue_team,
    max_rounds=3,
    verbose=True
)

consensus, result = debate.generate_with_debate(
    topic="The benefits of renewable energy",
    temperature=0.6
)

print(f"Original claim: {result.original_claim.text}")
print(f"Challenges: {len(result.challenges)}")
print(f"Final consensus: {result.final_consensus}")
print(f"Confidence: {result.confidence_score:.2f}")
```

### **9. Comprehensive Benchmarking**

```python
from src.benchmarks.mind_meld_benchmark import MindMeldBenchmark, BenchmarkConfig

benchmark = MindMeldBenchmark(verbose=True)

configs = [
    BenchmarkConfig(
        strategy_name="perplexity",
        models=['google/gemma-2-2b-it', 'Qwen/Qwen2-1.5B-Instruct'],
        prompt="Explain machine learning",
        max_tokens=100
    ),
    BenchmarkConfig(
        strategy_name="speculative",
        models=['TinyLlama/TinyLlama-1.1B-Chat-v1.0', 'google/gemma-2-9b-it'],
        prompt="Explain machine learning",
        max_tokens=100
    )
]

# Run benchmarks
results = benchmark.run_benchmark_suite(configs, engines_factory)

# Generate report
benchmark.generate_report("benchmark_report.html")
benchmark.save_results_json("results.json")
```

### **10. KV Cache Compression**

```python
from src.infrastructure.cache_manager import KVCacheCompressor

compressor = KVCacheCompressor(
    compression_ratio=0.5,  # 50% compression
    quantization_bits=8
)

# Compress KV cache before transferring between models
compressed, metadata = compressor.compress_cache(kv_cache, layer_idx=0)
print(f"Compressed {metadata['compression_ratio']:.1%}")

# Decompress for target model
decompressed = compressor.decompress_cache(compressed, metadata)
```

### **11. Model Cache with LRU Eviction**

```python
from src.infrastructure.cache_manager import ModelCache

cache = ModelCache(max_vram_mb=16384, verbose=True)

# Load models on-demand
model1 = cache.get_model('google/gemma-2-9b-it', 'pytorch', loader_func)
model2 = cache.get_model('codellama/CodeLlama-7b-Instruct-hf', 'pytorch', loader_func)

# Automatically evicts LRU when VRAM full
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Evictions: {stats['evictions']}")
```

### **12. Async Model Loading**

```python
from src.infrastructure.cache_manager import AsyncModelLoader

models_to_load = [
    ('google/gemma-2-2b-it', 'pytorch'),
    ('Qwen/Qwen2-1.5B-Instruct', 'pytorch')
]

# Load in parallel
loaded_models = AsyncModelLoader.load_models_parallel_sync(
    models_to_load,
    loader_func,
    max_concurrent=2
)

print(f"Loaded {len(loaded_models)} models in parallel")
```

### **13. Streaming Generation**

```python
from src.infrastructure.cache_manager import StreamingGenerator
import asyncio

generator = StreamingGenerator(engine)

async def stream_example():
    async for token in generator.generate_stream(
        prompt="Explain quantum computing",
        max_tokens=100
    ):
        print(token, end='', flush=True)

asyncio.run(stream_example())
```

### **14. Configuration Presets**

```python
from src.mind_meld.presets import get_preset, PresetType, list_presets

# List available presets
for preset_type, description in list_presets():
    print(f"{preset_type.value}: {description}")

# Get preset
preset = get_preset(PresetType.CODE_GENERATION)
print(f"Models: {preset.models}")
print(f"Strategy: {preset.strategy}")
print(f"Temperature: {preset.temperature}")

# Or get recommended preset
from src.mind_meld.presets import get_recommended_preset

preset = get_recommended_preset("Write a creative story about space")
# Returns: PresetType.CREATIVE_WRITING
```

## 🎯 Complete Usage Examples

### Example 1: Code Generation with Maximum Quality

```python
from src.core.model_registry import ModelSelector
from src.mind_meld.presets import get_preset, PresetType
from src.mind_meld.advanced.feedback_loop import FeedbackLoop, FeedbackType

# Get code generation preset
preset = get_preset(PresetType.CODE_GENERATION)

# Load models
selector = ModelSelector(available_vram_mb=16384)
models = selector.select_for_strategy('moe', task="code generation", num_models=2)

# Setup feedback loop for quality
generator = load_model(models[0])
critic = load_model(models[1])

loop = FeedbackLoop(generator, critic, max_iterations=2)

result = loop.run_loop(
    prompt="Write a Python function to implement quicksort",
    max_tokens=200,
    aspects=[FeedbackType.GRAMMAR, FeedbackType.COMPLETENESS]
)

print(result.revised_text)
```

### Example 2: Fast Generation with Speculative Decoding

```python
from src.mind_meld.presets import get_preset, PresetType
from src.mind_meld.advanced.speculative_decoding import SpeculativeDecoder

preset = get_preset(PresetType.FAST_GENERATION)

# Speculative decoding setup
draft = load_model('TinyLlama/TinyLlama-1.1B-Chat-v1.0')
target = load_model('Qwen/Qwen2-1.5B-Instruct')

decoder = SpeculativeDecoder(draft, target, k=4)

generated, stats = decoder.generate(
    "Write a short story about a robot",
    max_tokens=150
)

print(f"Generated at {stats['tokens_per_second']:.1f} tok/s")
print(f"Speedup: {stats['avg_speedup']:.2f}x")
```

### Example 3: Research Analysis with Adversarial Debate

```python
from src.mind_meld.presets import get_preset, PresetType
from src.mind_meld.advanced.adversarial import AdversarialDebate
from src.mind_meld.advanced.hierarchical_control import HierarchicalController

preset = get_preset(PresetType.RESEARCH_ANALYSIS)

# Hierarchical planning
meta = load_model('google/gemma-2-9b-it')
specialists = {
    PlanStep.ANALYZE: meta,
    PlanStep.PROVIDE_EVIDENCE: meta,
}

controller = HierarchicalController(meta, specialists)

# Generate with planning
generated, plan = controller.generate_with_planning(
    objective="Analyze the impact of AI on employment",
    max_steps=5
)

# Then fact-check with adversarial debate
red = load_model('google/gemma-2-9b-it')
blue = load_model('mistralai/Mistral-7B-Instruct-v0.2')

debate = AdversarialDebate(red, blue)
consensus, result = debate.generate_with_debate(generated)

print(f"Final output (fact-checked):\n{consensus}")
```

## 📊 Benchmarking Your Configuration

```python
from src.benchmarks import MindMeldBenchmark, BenchmarkConfig

benchmark = MindMeldBenchmark()

# Test multiple strategies
strategies = ['perplexity', 'semantic', 'pattern', 'fixed']
results = []

for strategy in strategies:
    config = BenchmarkConfig(
        strategy_name=strategy,
        models=['google/gemma-2-2b-it', 'Qwen/Qwen2-1.5B-Instruct'],
        prompt="Explain neural networks",
        max_tokens=100
    )

    result = benchmark.run_single_benchmark(config, meld_engine)
    results.append(result)

    print(f"{strategy}: {result.tokens_per_second:.2f} tok/s, "
          f"perplexity: {result.avg_perplexity:.2f}")

# Generate comparison report
benchmark.generate_report("comparison.html")
```

## 🔧 Best Practices

1. **Start with Presets**: Use built-in presets for your use case
2. **Benchmark First**: Test strategies on your hardware before production
3. **Use Model Cache**: Reduce memory overhead with LRU cache
4. **Enable Speculative for Speed**: 2-3x speedup for interactive apps
5. **Use ABE for Accuracy**: Agreement-based ensembling for critical tasks
6. **Combine Techniques**: Hierarchical + Feedback + Adversarial = highest quality
7. **Monitor Performance**: Use benchmarking suite regularly
8. **GPU/NPU Aware**: Model selector handles hardware constraints

## 🚀 Performance Tips

- **Speculative Decoding**: Best for real-time applications
- **Contrastive Decoding**: Best for specialized content
- **MoE Routing**: Best for mixed content (code + prose)
- **Feedback Loops**: Best for quality-critical applications
- **Adversarial**: Best for factual accuracy requirements

## 📝 Notes

All implementations are production-ready and extensively documented. Each module includes comprehensive docstrings and type hints for easy integration.
