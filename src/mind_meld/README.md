# Mind Meld (⚡ quick guide)

Mind Meld is GAMMA’s playground for running **multiple models at the same time**.  You can let them vote on every token, hand off the pen mid-sentence, or route the prompt to specialists on the fly.  This note keeps only the combos that are practical, fast, and fun.

---

## 1. Core moves

| Move | What happens | When to use |
|------|---------------|-------------|
| **Token Ensemble** (`--use-blending`) | Every model stays active; logits are merged before sampling the next token. | Create a single voice from several models. |
| **Token Handoff** (swap strategies) | Only one model writes at a time; the active model can change on punctuation, confidence drops, etc. | Give specialists turns (code vs story, large vs small). |
| **MoE Router** (`--use-moe-router`) | The prompt is classified each step (code, dialogue, math, etc.) and dispatched to the best model. | You have clearly specialised models. |
| **Contrastive Decoding** (`--use-contrastive-decoding`) | An expert model’s logits are boosted while “generic” models are subtracted. | Let a big model steer, keep faster models around for safety. |

You can mix these moves: e.g. blend two models most of the time but still swap to a third specialist when punctuation hits.

---

## 2. Five quick recipes

```bash
# 1. Simple ensemble (equal weight)
python gamma.py mind-meld \
  --models "llamacpp:modelA.gguf" "llamacpp:modelB.gguf" \
  --use-blending --blend-strategy weighted_average

# 2. Confidence voting (trust whichever model is certain)
python gamma.py mind-meld \
  --models "pytorch:google/gemma-3-4b-it" "pytorch:Qwen/Qwen2-7B-Instruct" \
  --use-blending --blend-strategy confidence_weighted --confidence-power 1.5

# 3. Agreement-first swap (ABE + punctuation handoff)
python gamma.py mind-meld \
  --models model1 model2 \
  --use-abe --swap-strategy pattern

# 4. MoE router (code vs story)
python gamma.py mind-meld \
  --models "codellama/CodeLlama-13b-hf" "mistralai/Mistral-7B-Instruct-v0.2" \
  --use-moe-router --adaptive-routing

# 5. Expert amplification (contrastive decoding)
python gamma.py mind-meld \
  --models "openai/gpt-oss-20b" "google/gemma-3-27b-it" \
  --use-contrastive-decoding --expert-model 0 --amateur-models 1 --alpha 0.5
```

Tip: add `--prompt "Your starting text" --steps 200 --visualize` to any command above.

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

| Flag | Behaviour |
|------|-----------|
| `--swap-strategy fixed_interval --fixed-interval 4` | Rotate every N tokens. |
| `--swap-strategy pattern` | Swap on punctuation / newline (default). |
| `--swap-strategy confidence --min-confidence 0.7` | Hand off when the active model becomes uncertain. |
| `--swap-strategy perplexity` | Similar to confidence, driven by perplexity spikes. |
| `--swap-strategy semantic` | Detect topic drift via embeddings. |
| `--swap-strategy round_robin` | Strict turn taking. |
| `--swap-strategy random --random-probability 0.3` | Occasional surprise swaps. |

Combine with `--use-blending` for “blend most of the time, but still give someone else the mic occasionally”.

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

## 8. Want to tweak the internals?

- **Blending & ABE:** `src/mind_meld/core/blending.py`, `core/abe_ensemble.py`
- **MoE router:** `src/mind_meld/advanced/moe_router.py`
- **Contrastive decoding:** `src/mind_meld/advanced/contrastive_decoding.py`
- **Bridging (KV, hidden, attention):** `src/mind_meld/bridges/state_bridge.py`
- **Swap strategies:** `src/mind_meld/strategies/`

The code is modular—feel free to add your own strategy or consensus module, hook it into `MeldEngine`, and document a new recipe at the top of this page.

Enjoy blending brains! 🧠⚡
