# Mind Meld (⚡ quick guide)

Mind Meld is GAMMA’s playground for running **multiple models at the same time**.  You can let them vote on every token, hand off the pen mid-sentence, or route the prompt to specialists on the fly.  This note keeps only the combos that are practical, fast, and fun.

---

## 1. Core moves

| Move | What happens | When to use |
|------|---------------|-------------|
| **Token Ensemble** (`--use-blending`) | Every model stays active; logits are merged before sampling the next token. | Create a single voice from several models. |
| **Token Handoff** (swap strategies) | Only one model writes at a time; the active model can change on punctuation, confidence drops, etc. | Give specialists turns (code vs story, large vs small). |
| **MoE Router** (programmatic) | The prompt is classified each step (code, dialogue, math, etc.) and dispatched to the best model. | You have clearly specialised models. |
| **Contrastive Decoding** (programmatic) | An expert model's logits are boosted while "generic" models are subtracted. | Let a big model steer, keep faster models around for safety. |

**Note:** MoE Router and Contrastive Decoding are available via the Python API but not yet exposed via CLI flags.

You can mix these moves: e.g. blend two models most of the time but still swap to a third specialist when punctuation hits.

---

## 2. Quick recipes

### CLI Commands

```bash
# 1. Simple ensemble with blending
python gamma.py mind-meld \
  --models "llamacpp:modelA.gguf" "llamacpp:modelB.gguf" \
  --use-blending

# 2. Agreement-Based Ensembling with punctuation handoff
python gamma.py mind-meld \
  --models model1 model2 \
  --use-abe --strategy pattern

# 3. Fixed interval swap (rotate every 3 tokens)
python gamma.py mind-meld \
  --models model1 model2 \
  --strategy fixed --fixed-interval 3

# 4. Perplexity-based swap
python gamma.py mind-meld \
  --models model1 model2 \
  --strategy perplexity
```

Tip: add `--prompt "Your starting text" --steps 200` to any command above.

### Programmatic API (for MoE Router & Contrastive Decoding)

```python
from src.mind_meld.core.meld_engine import MeldEngine
from src.mind_meld.advanced.moe_router import MoERouter
from src.mind_meld.advanced.contrastive_decoding import ContrastiveDecoder

# MoE Router example
moe_router = MoERouter(engines, adaptive=True)
selected_engine = moe_router.route(prompt)

# Contrastive Decoding example
decoder = ContrastiveDecoder(expert_engine, amateur_engines, alpha=0.5)
logits = decoder.decode(input_ids)
```

---

## 3. Logit blending strategies (when `--use-blending`)

| Strategy | One-liner |
|----------|-----------|
| `weighted_average` | Plain mean. Good baseline. |
| `confidence_weighted` | Low-entropy distributions get more weight. |
| `dynamic_weighted` | Learns who to trust based on perplexity / entropy over time. |
| `attention_weighted` | Gives weight to the model most focused on the current context. |
| `ensemble_voting` | Majority vote on the top-k tokens; conservative, high agreement. |
| `learned`, `hierarchical` | Experimental gating layers (see `core/blending.py`). |
| `--use-abe` (Agreement-Based Ensembling) | Bonus layer: detect surface-form matches even when tokenizers differ. |

You can combine `--use-blending` with swap strategies or MoE. When swapping is active, the “current” model simply receives a larger weight in the blend.

---

## 4. Sharing context and attention

Mind Meld can transfer internal state when models take turns:

| Component | Flag / behaviour | Why it’s cool |
|-----------|------------------|---------------|
| **KV cache** | On by default. Uses `KVCacheTranslator` to copy / project keys & values between models. | The next model starts with the full conversation memory instead of reprocessing the prompt. |
| **Hidden states** | Auto-projected when dimensions differ. | Keeps feature representations aligned across architectures. |
| **Attention maps** | Preserved when `swap_components` include `attention`. | Maintains focus even if tokenization changes. |
| **Raw context** | Sliding/truncation (`BridgeConfig.context_window_alignment`). | Handles models with mismatched window sizes. |

Most of this “just works” out of the box. For incompatible architectures, the bridge falls back to projection and logs a warning.

---

## 5. Swap strategies (token handoff)

### CLI-Supported Strategies

| Flag | Behaviour |
|------|-----------|
| `--strategy fixed --fixed-interval 4` | Rotate every N tokens (default: 3). |
| `--strategy pattern` | Swap on punctuation / newline. |
| `--strategy perplexity` | Hand off when perplexity spikes. |
| `--strategy round_robin` | Strict turn taking. |
| `--strategy random` | Occasional surprise swaps. |

### Programmatic-Only Strategies

These strategies are available via `src/mind_meld/strategies/` but not yet CLI-exposed:

- `confidence` - Hand off when the active model becomes uncertain
- `semantic` - Detect topic drift via embeddings

Combine with `--use-blending` for "blend most of the time, but still give someone else the mic occasionally".

---

## 6. Model-mixing tips

1. **GGUF pairs:** use the `llamacpp` engine for every model; Mind Meld converts vocabularies automatically.  You get logits, KV cache sharing, and strong CPU/GPU performance.
2. **HF Transformers:** mix and match PyTorch models (`pytorch` / `pytorch_cuda` / ROCm builds). Vocabulary alignment happens via the same translator.
3. **Ollama:** great for quick experiments, but the HTTP API does **not** expose logits. For real ensembles, grab the GGUF path (`ollama show <model> --modelfile`) and run it with `llamacpp` inside GAMMA.
4. **Large + small:** try a 20B model as the “expert” and a 7B as a fast follower. Confidence-weighted blending usually gives the big model 70–80% influence but keeps the small one primed for fallback.

---

## 7. Visuals & telemetry

- `--visualize` launches the swap log and contribution bars in the terminal.  Great for demos.
- `--use-stats-tracker --stats-file meld.json` writes per-token metrics (swap count, confidence, agreement rate).
- `tools/verify_mind_meld.py` gives a quick sanity check of your configuration.

---

## 8. Headless mode (testing & automation)

For CI pipelines, scripting, or running without terminal interaction:

```bash
# Run headless with a prompt
python gamma.py mind-meld \
  --models model1 model2 \
  --headless --prompt "Once upon a time" --steps 50

# Quiet mode suppresses all output except errors
python gamma.py mind-meld \
  --models model1 model2 \
  --headless --quiet --prompt "Test" --steps 10
```

Headless mode:
- Skips all user prompts and interactive UI
- Suppresses visualization exports
- Returns generated text programmatically
- Works with all blending/swap strategies

For programmatic access, use `MeldEngine._run_headless()` directly:

```python
from src.mind_meld.core.meld_engine import MeldEngine

meld = MeldEngine(engines, args)
result_text = meld._run_headless()
```

---

## 9. Want to tweak the internals?

- **Blending & ABE:** `src/mind_meld/core/blending.py`, `core/abe_ensemble.py`
- **MoE router:** `src/mind_meld/advanced/moe_router.py`
- **Contrastive decoding:** `src/mind_meld/advanced/contrastive_decoding.py`
- **Bridging (KV, hidden, attention):** `src/mind_meld/bridges/state_bridge.py`
- **Swap strategies:** `src/mind_meld/strategies/`

The code is modular—feel free to add your own strategy or consensus module, hook it into `MeldEngine`, and document a new recipe at the top of this page.

---

## 10. Translators (vocabulary alignment)

When combining models with different tokenizers, Mind Meld uses translators to bridge the gap:

| File | Purpose |
|------|---------|
| `translators/vocabulary_aligner.py` | Align tokens between different vocabularies |
| `translators/vocabulary_aligner_enhanced.py` | Enhanced alignment with subword matching |
| `translators/kv_cache_translator.py` | Project KV cache between model architectures |
| `translators/sparse_ot_projection.py` | Optimal transport for embedding space alignment |
| `translators/vocabulary_translator.py` | Token-level translation between models |

These are automatically used when models have incompatible tokenizers.

---

## 11. Additional Advanced Features

Beyond the core strategies, Mind Meld includes experimental features:

| Feature | File | Description |
|---------|------|-------------|
| **Speculative Decoding** | `advanced/speculative_decoding.py` | Use small model to draft, large model to verify |
| **Gemma Speculative** | `advanced/gemma_speculative.py` | Speculative decoding optimized for Gemma models |
| **Adversarial Debate** | `advanced/adversarial.py` | Models argue to refine outputs |
| **Multi-LoRA Routing** | `advanced/multi_lora_router.py` | Route to specialized LoRA adapters |
| **Hierarchical Control** | `advanced/hierarchical_control.py` | Layered model orchestration |
| **Homogeneous Ensemble** | `advanced/homogeneous_ensemble.py` | Ensemble of identical model instances |
| **Feedback Loop** | `advanced/feedback_loop.py` | Iterative refinement with feedback |
| **Syntactic Strategy** | `strategies/semantic_strategy.py` | Swap based on syntactic roles (SyntacticRoleStrategy) |

These are experimental and may require additional configuration. See each file for usage details.

---

Enjoy blending brains!
