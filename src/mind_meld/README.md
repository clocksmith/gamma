# Mind Meld (⚡ quick guide)

Mind Meld is GAMMA’s playground for running **multiple models at the same time**.  You can let them vote on every token, hand off the pen mid-sentence, or route the prompt to specialists on the fly.  This note keeps only the combos that are practical, fast, and fun.

---

## 1. Core moves

| Move | What happens | When to use |
|------|---------------|-------------|
| **Token Ensemble** (`--use-blending`) | Every model stays active; logits are merged before sampling the next token. | Create a single voice from several models. |
| **Token Handoff** (swap strategies) | Only one model writes at a time; the active model can change on punctuation, confidence drops, etc. | Give specialists turns (code vs story, large vs small). |
| **MoE Router** (`--use-moe-router`) | The prompt is classified each step (code, dialogue, math, etc.) and dispatched to the best model. | You have clearly specialised models. |
| **Contrastive Decoding** (`--use-contrastive`) | An expert model's logits are boosted while "generic" models are subtracted. | Let a big model steer, keep faster models around for safety. |
| **Speculative Decoding** (`--use-speculative`) | Draft model proposes tokens, target model verifies in parallel. 2-3x speedup. | Speed up generation with small+large model pairs. |
| **Feedback Loop** (`--use-feedback-loop`) | Generator creates, critic refines iteratively. | Self-critique for higher quality output. |
| **Adversarial Debate** (`--use-adversarial`) | Red team proposes, blue team challenges to reach consensus. | Fact-checking and reasoning tasks. |
| **Hierarchical Control** (`--use-hierarchical`) | Meta-model plans, specialist models execute each step. | Complex multi-step generation. |

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

# 3. Fixed interval swap (rotate every 8 tokens)
python gamma.py mind-meld \
  --models model1 model2 \
  --strategy fixed --fixed-interval 8 \
  --translate-logits  # optional: decode using the next model's vocab (experimental)

# 4. Perplexity-based swap
python gamma.py mind-meld \
  --models model1 model2 \
  --strategy perplexity

# 5. Speculative decoding for 2-3x speed
python gamma.py mind-meld \
  --models pytorch:google/gemma-2-2b-it pytorch:google/gemma-3-1b-it \
  --use-speculative --speculative-k 4

# 6. Content-aware MoE routing
python gamma.py mind-meld \
  --models model1 model2 \
  --use-moe-router

# 7. Contrastive decoding (expert vs amateur)
python gamma.py mind-meld \
  --models pytorch:large-model pytorch:small-model \
  --use-contrastive

# 8. Feedback loop refinement
python gamma.py mind-meld \
  --models model1 model2 \
  --use-feedback-loop

# 9. Adversarial debate mode
python gamma.py mind-meld \
  --models model1 model2 \
  --use-adversarial
```

Tip: add `--prompt "Your starting text" --steps 200` to any command above.
If you are using instruction-tuned models, GAMMA applies chat templates when available. Use `--prompt-system`
or `--no-default-system` to control the system prompt. If a tokenizer rejects a system role, GAMMA retries
with a user-only template.
If chat templates differ across models, swaps can be order-sensitive. GAMMA now auto-enables
`--shared-chat-template` when every model supports chat templates; use `--no-shared-chat-template`
to keep per-model templates, or `--no-prompt-chat-template` to use a raw prompt.
If you want swap cadence but less order sensitivity, add `--soft-swap` to blend models each
step while still boosting the active model (adjust with `--soft-swap-weight`).

### Programmatic API

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
| **KV cache** | On by default. Uses direct sharing when prompt prefixes match; otherwise replays the missing suffix through the target model to rebuild its cache. | The next model starts with full conversation memory. Replay is lossless but adds compute; the replay path aligns full-token prefixes to avoid tokenizer boundary drift. KV cache translation is optional via `--allow-kv-cache-translation` and remains experimental; safety checks skip translation unless `--force-kv-cache-translation` is set, and it still falls back to replay if translation fails. |
| **Hidden states** | Auto-projected when dimensions differ. | Keeps feature representations aligned across architectures. |
| **Attention maps** | Preserved when `swap_components` include `attention`. | Maintains focus even if tokenization changes. |
| **Raw context** | Sliding/truncation (`BridgeConfig.context_window_alignment`). | Handles models with mismatched window sizes. |

Most of this “just works” out of the box. For incompatible architectures, the bridge falls back to projection and logs a warning.

Note: swap strategies decode using the active model's vocabulary by default. If you
want to translate logits into the next model's vocab during swaps, pass
`--translate-logits` (experimental).

---

## 5. Swap strategies (token handoff)

### CLI-Supported Strategies

| Flag | Behaviour |
|------|-----------|
| `--strategy fixed --fixed-interval 8` | Rotate every N tokens (default: 8). |
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
5. **OpenAI/HF Inference APIs:** these wrappers do not expose logits, so Mind Meld cannot use them. Use native engines instead.
6. **KV cache sharing:** Mind Meld prefers direct KV transfer when prompt prefixes match. When they differ, it replays the missing suffix through the target model to rebuild a correct cache instead of copying incompatible entries. Architecture translation remains experimental and is only attempted when `--allow-kv-cache-translation` is set; safety checks skip translation unless `--force-kv-cache-translation` is provided, and it may still fall back to replay.

---

## 7. Visuals & telemetry

- Visualization (swap log and contribution bars) is shown by default in interactive runs.
- `--use-stats-tracker --stats-file meld.json` writes per-token metrics (swap count, confidence, agreement rate).
- `--meld-diagnostics` prints a summary of KV cache bridging, replay, and vocab-translation usage at the end of the run.
- `--no-step-delay` disables the 1-second pause between steps in interactive runs.
- `--summary-only` prints only the final output and brief stats (no per-round or live stats output; stats tracker stays off unless enabled).
- `--max-sentences` stops Mind Meld after N sentences in the generated output.
- `--stop-text` stops Mind Meld when the generated output contains a specific string (repeatable).
- `--order-neutral` uses weighted average to reduce swap-order sensitivity (alias for `--use-weighted-average`).
- `--repetition-penalty` reduces repeated tokens during sampling (default: 1.1).
- `tools/verify_mind_meld.py` gives a quick sanity check of your configuration.

Mind Meld auto stops on common chat template end markers when chat templates are
used. Use `--stop-text` to override or add markers. In `--summary-only` mode,
`--max-sentences` trims any trailing incomplete sentence for cleaner output.

---

## 8. Headless mode (testing & automation)

For CI pipelines, scripting, or running without terminal interaction:

```bash
# Run headless with a prompt
python gamma.py mind-meld \
  --models model1 model2 \
  --headless --prompt "Once upon a time" --steps 50

```

Headless mode:
- Skips all user prompts and interactive UI
- Skips visualization exports
- Returns generated text programmatically
- Works with all blending/swap strategies
- Applies chat templates automatically for instruction-tuned models (disable with `--no-prompt-chat-template`)
- Default system prompt helps avoid repetitive output (override with `--prompt-system` or disable with `--no-default-system`)

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

You can choose the alignment strategy via `--alignment-strategy`:
- `intersection`: fast, only shared tokens
- `align`: decode/encode surface-form alignment
- `subword`: subword decomposition mapping
- `semantic_map`: lightweight semantic mapping
- `unk`: map missing tokens to the target unknown token
- `auto`: use the default strategy from config

For large vocabularies, `align` and `semantic_map` may take a few minutes the first time they build a mapping.

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
