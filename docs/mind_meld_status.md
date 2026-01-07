# Mind Meld Status and Notes

Date: 2026-01-06 (updated)

This note captures the current Mind Meld behavior, recent debugging outcomes,
and what still needs work. It is written for operators who want a clear view of
what works today and where the risks are.

## What Works

- Single-model inference is stable with PyTorch engines (Gemma 2B/3B tested).
- Mind Meld runs with swaps, summary-only output, and chat templates.
- Shared chat templates reduce order sensitivity when templates differ.
- Output trimming via `--max-sentences` avoids trailing partial sentences in
  summary-only mode.
- KV cache replay works across mismatched tokenizers and architectures.
- Warning noise is suppressed by default (POT and Keras `np.object` warnings).
- Model-pair guardrails automatically prefer replay when compatibility is poor.
- Tokenizer-aligned KV translation for cross-vocabulary models.

## Mind Meld Capabilities (Current)

Mind Meld can combine models via:

- Swap strategies (all now exposed in CLI): `fixed`, `fixed_interval`, `pattern`,
  `round_robin`, `random`, `confidence`, `perplexity`, `attention`, `weighted`,
  `semantic`.
- Blending: `--use-blending` with strategies like `weighted_average`,
  `confidence_weighted`, `dynamic_weighted`, `attention_weighted`,
  `ensemble_voting`, and `learned`.
- Agreement-Based Ensembling: `--use-abe` (token-surface agreement).
- Per-model personas: `--persona` flag (repeat for each model) for different
  system prompts per model.
- Optional helpers: `--use-speculative`, `--use-contrastive`, `--use-moe-router`,
  `--use-feedback-loop`, `--use-adversarial`, `--use-hierarchical`.
- Soft swaps: `--soft-swap` keeps cadence while blending every step.
- Order neutral blending: `--order-neutral` (alias for weighted average).
- Enhanced mode: `--use-enhanced` enables translate-logits, diagnostics, and
  stats tracking together.

Mind Meld requires logits. Wrapper engines (OpenAI/HF Inference/Ollama APIs)
cannot provide logits, so Mind Meld uses native engines (pytorch, llamacpp,
vllm, mlx, etc.).

## KV Cache Bridging Policy

KV cache transfer is **safe** only when prompt prefixes and tokenizers match.
When they do not, Mind Meld replays the missing suffix to rebuild a valid cache.
This replay is lossless but adds compute.

### Model-Pair Guardrails (New)

Mind Meld now includes automatic guardrails that prefer replay when model pairs
are incompatible. Guardrails trigger when:

- Compatibility level is POOR or INCOMPATIBLE (score < 0.45)
- Vocabulary overlap is less than 50%
- Different architectures AND hidden size mismatch
- Layer count mismatch (KV cache is per-layer)
- KV cache not bridgeable without translation flag

Use `--force-kv-cache-translation` to bypass guardrails. Diagnostic counter
`guardrail_replay` tracks how often guardrails redirected to replay.

### Tokenizer-Aligned Translation (New)

When `--allow-kv-cache-translation` is enabled and models have different
vocabularies, Mind Meld now attempts character-level token alignment. This maps
KV cache positions based on text spans rather than assuming 1:1 token
correspondence. This reduces gibberish from misaligned attention patterns.

### KV Cache Translation Settings

KV cache translation remains **experimental**. It is only attempted when:

- `--allow-kv-cache-translation` is set, and
- safety checks pass (same tokenizer type/vocab, matching layers and attention
  geometry, and same model name), or
- `--force-kv-cache-translation` bypasses safety checks (unsafe).

Use `--meld-diagnostics` to see which path was used:

- `kv_cache_attempts` and `kv_cache_translated` > 0 indicate translation.
- `kv_cache_replay` > 0 indicates replay fallback.
- `guardrail_replay` > 0 indicates guardrail-triggered replays.

## Best Practices

### Model Selection

1. **Same architecture family**: Prefer models from the same family (e.g.,
   Llama+Mistral+CodeLlama) for best KV cache compatibility.
2. **Similar sizes**: Models with matching hidden dimensions and layer counts
   enable direct KV bridging without translation overhead.
3. **Shared tokenizers**: Models trained on the same tokenizer (e.g., all using
   Llama tokenizer) avoid vocabulary translation losses.

### Configuration Recipes

**Conservative (stable output)**:
```bash
python gamma.py mind-meld \
  --meld-models pytorch:model-a pytorch:model-b \
  --swap-strategy pattern \
  --shared-chat-template \
  --meld-diagnostics
```

**Experimental (cross-architecture)**:
```bash
python gamma.py mind-meld \
  --meld-models pytorch:llama-7b pytorch:gemma-7b \
  --swap-strategy fixed_interval --fixed-interval 8 \
  --allow-kv-cache-translation \
  --shared-chat-template \
  --use-enhanced
```

**Blending (all models contribute)**:
```bash
python gamma.py mind-meld \
  --meld-models pytorch:model-a pytorch:model-b pytorch:model-c \
  --use-blending --blend-strategy confidence_weighted \
  --order-neutral
```

**Per-model personas (identical models, different personalities)**:
```bash
python gamma.py mind-meld \
  --models pytorch:google/gemma-3-1b-it pytorch:google/gemma-3-1b-it \
  --persona "You are an optimistic futurist." \
  --persona "You are a cautious skeptic." \
  --strategy fixed_interval --interval 8 \
  --prompt "What is the future of AI?"
```

**Expert panel (3 personas with ABE)**:
```bash
python gamma.py mind-meld \
  --models pytorch:gemma-1b pytorch:gemma-1b pytorch:gemma-1b \
  --persona "You are a scientist who uses data and evidence." \
  --persona "You are a philosopher who asks deep questions." \
  --persona "You are an artist who thinks in metaphors." \
  --use-abe \
  --prompt "What is consciousness?"
```

**Soft swap with blending (smooth transitions)**:
```bash
python gamma.py mind-meld \
  --models pytorch:gemma-1b pytorch:gemma-1b \
  --soft-swap \
  --use-blending --blend-strategy confidence_weighted \
  --prompt "Explain quantum computing"
```

**Draft/refine (small model drafts, large validates)**:
```bash
python gamma.py mind-meld \
  --models pytorch:gemma-1b pytorch:gemma-2b \
  --use-speculative \
  --shared-chat-template \
  --prompt "Write a short story"
```

**Semantic swapping (swap on topic change)**:
```bash
python gamma.py mind-meld \
  --models pytorch:llama-7b pytorch:codellama-7b \
  --swap-strategy semantic --semantic-threshold 0.7 \
  --prompt "Explain REST APIs with code examples"
```

**Round robin (alternating models)**:
```bash
python gamma.py mind-meld \
  --models pytorch:model-a pytorch:model-b \
  --swap-strategy round_robin \
  --meld-diagnostics \
  --prompt "What are the pros and cons of remote work?"
```

**Confidence routing (swap on uncertainty)**:
```bash
python gamma.py mind-meld \
  --models pytorch:general-model pytorch:specialist-model \
  --swap-strategy confidence --confidence-threshold 0.8 \
  --prompt "Explain machine learning basics"
```

**Perplexity routing (swap on confusion)**:
```bash
python gamma.py mind-meld \
  --models pytorch:model-a pytorch:model-b \
  --swap-strategy perplexity --perplexity-threshold 50.0 \
  --prompt "Describe the history of computing"
```

### Tactics Summary

| Tactic | Best For | Model Setup | Key Flags |
|--------|----------|-------------|-----------|
| Expert Panel | Diverse perspectives | 3x identical | `--persona` x3, `--use-abe` |
| Draft/Refine | Quality + speed | small + large | `--use-speculative` |
| Confidence Routing | Uncertainty handling | general + specialist | `--strategy confidence` |
| Perplexity Swap | Detecting confusion | 2+ any | `--strategy perplexity` |
| Semantic Swap | Topic-based routing | general + domain | `--strategy semantic` |
| Weighted Blend | Smooth mixing | 2-3 same family | `--use-blending --order-neutral` |
| Soft Swap | Gradual transitions | 2 similar | `--soft-swap` |

### What Works Best Today

1. **Identical models + personas** - Full KV sharing, different perspectives, no translation overhead
2. **Same family, similar sizes** - Minimal compatibility issues, fast KV transfer
3. **ABE with 3+ models** - Consensus reduces hallucination, best with identical models
4. **Draft/refine pattern** - Small model speed + large model quality

### What Requires Caution

1. **Cross-architecture** - Works but relies on replay (slower)
2. **Different vocab sizes** - Blending mode has known index bug
3. **Force KV translation** - Produces garbage without matching layer counts

### Per-Model Personas

The `--persona` flag allows different system prompts for each model. This is
ideal for:

- **Debate scenarios**: optimist vs pessimist, pro vs con
- **Expert panels**: scientist + philosopher + artist
- **Perspective blending**: technical + creative + ethical viewpoints
- **Role-play**: different characters contributing to a story

Key observations:
- First persona tends to influence initial tone strongly
- Identical models + different personas = ideal setup (KV cache shares directly)
- ABE works well for finding consensus tokens across perspectives
- Soft-swap can cause stuttering with very contrasting personas

### Debugging Swaps

1. Enable `--meld-diagnostics` to see KV cache path decisions.
2. Enable `--verbose` to see swap events and model transitions.
3. Use `--summary-only` with `--max-sentences 5` for quick quality checks.
4. Check `guardrail_replay` counter to see if guardrails are triggering.

### Performance Tips

1. Use `--soft-swap` to reduce hard swap overhead while still varying model
   influence.
2. Use `--headless` for batch/scripted runs without UI output.
3. For benchmarking, use `src/benchmarks/mind_meld_benchmark.py` with
   `benchmark_kv_cache_strategies()` to compare KV handling approaches.

## Open Items / TODO

### Completed
- ~~Design a near-lossless KV translation algorithm for different checkpoints.~~ (Tokenizer alignment added)
- ~~Add token-alignment-aware KV translation (not just shape projection).~~ (Done)
- ~~Expand tests for swap-order sensitivity and prompt-template consistency.~~ (Done)
- ~~Expose additional swap strategies (confidence/semantic) in the CLI.~~ (Done)
- ~~Improve evaluation harness for stability across model orderings.~~ (Stability benchmarks added)
- ~~Add model-pair guardrails to auto-prefer replay when incompatible.~~ (Done)
- ~~Fix engine comparison bug when using identical models.~~ (Done)

### Remaining Work

**Recently completed:**
- ~~Further optimize tokenizer alignment for long sequences~~ (Binary search + caching added)
- ~~Add regression test suite for KV replay latency~~ (tests/test_kv_cache_latency.py)
- ~~Fix blending mode vocab mismatch bug~~ (2D array handling fixed in blending.py)

**Unsolved Research Problems:**

These are fundamental challenges that require research-level solutions:

1. **Cross-Architecture KV Cache Translation**
   - Problem: Models with different layer counts (e.g., 18 vs 26 layers) cannot share KV cache directly
   - Challenge: Which layer in Model A maps to which layer in Model B?
   - Current behavior: Guardrails block, falls back to replay (safe but slow)

2. **Hidden Dimension Projection**
   - Problem: Models with different hidden sizes (e.g., 2048 vs 2304) store attention in incompatible shapes
   - Challenge: Need learned projection matrices to map between representation spaces
   - Potential approach: Train adapter networks on parallel model outputs

3. **Semantic Attention Transfer**
   - Problem: Even with matching shapes, attention patterns have different *meanings* across separately-trained models
   - Challenge: Attention head 3 in Model A may encode syntax, while head 3 in Model B encodes semantics
   - This is essentially "neural network translation" - an open research problem

4. **Cross-Tokenizer KV Alignment (partially solved)**
   - Problem: Different tokenizers produce different token counts for same text
   - Partial solution: `TokenizerAlignedTranslation` maps positions via character spans
   - Remaining: Handle edge cases (BPE merges, special tokens, subword boundaries)

**Why `--force-kv-cache-translation` produces garbage:**
Forcing translation between incompatible architectures (Gemma 1B → Gemma 2B) attempts to copy 18-layer attention states into a 26-layer model. The misaligned internal representations cause the model to attend to wrong positions, producing incoherent output like "robots. to the rateing.ಣೆिंग."

The guardrails exist specifically to prevent this. Use `--force` only for research/debugging.
