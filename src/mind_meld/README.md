# Mind Meld

Mind Meld is GAMMA's multi-model generation system for token-level blending, swapping, routing, and diagnostics.

## What It Supports

| Capability | Flags | Use case |
|---|---|---|
| Token blending | `--use-blending`, `--blend-strategy ...` | Merge multiple model distributions |
| Token handoff | `--strategy ...` | Switch active model by rule |
| Agreement ensembling | `--use-abe` | Favor shared token choices |
| MoE routing | `--use-moe-router` | Route by content type |
| Speculative decode | `--use-speculative` | Small model drafts, larger verifies |
| Contrastive decoding | `--use-contrastive` | Expert steering vs generic model drift |
| Feedback/adversarial/hierarchical modes | `--use-feedback-loop`, `--use-adversarial`, `--use-hierarchical` | Iterative critique / debate / orchestration |

Mind Meld requires logits. Wrapper engines (OpenAI/HF Inference/Ollama API) are not suitable for full Mind Meld flows.

## Quick Start

### New CLI (preset + YAML oriented)

```bash
python tools/run_mind_meld_cli.py --preset creative
python tools/run_mind_meld_cli.py --preset debate --prompt "Is AI beneficial?"
python tools/run_mind_meld_cli.py gemma-1b gemma-2b --blend dynamic
python tools/run_mind_meld_cli.py configs/mind_meld/example-custom.yaml
python tools/run_mind_meld_cli.py --list-presets
python tools/run_mind_meld_cli.py --list-models
```

### Main GAMMA CLI

```bash
python gamma.py mind-meld --models model1 model2 --strategy pattern
python gamma.py mind-meld --models model1 model2 --use-blending --blend-strategy confidence_weighted
python gamma.py mind-meld --models model1 model2 --use-speculative
python gamma.py mind-meld --models model1 model2 --summary-only --max-sentences 2
```

## Configuration Model

Config sources apply in this order (highest first):

1. CLI flags
2. explicit config file (`--config` or positional `.yaml`)
3. preset (`--preset`)
4. built-in defaults

User alias file:

```yaml
# ~/.mind-meld.yaml
aliases:
  fast: "pytorch:google/gemma-3-1b-it"
  smart: "pytorch:google/gemma-3-4b-it"
  local: "llamacpp:/path/to/model.gguf"
```

## Strategy Reference

### Swap strategies

- `fixed_interval`
- `pattern`
- `perplexity`
- `round_robin`
- `random`
- `confidence`
- `semantic`

### Blend strategies

- `weighted_average`
- `confidence_weighted`
- `dynamic_weighted`
- `attention_weighted`
- `ensemble_voting`
- `learned` (experimental)

## Operational Status and Guardrails

Current stable behavior:

- PyTorch single-model inference is stable.
- Mind Meld runs with swap strategies, summary-only output, and chat templates.
- Shared chat templates reduce order sensitivity when templates differ.
- KV cache replay fallback is stable for incompatible tokenizer/model pairs.

KV bridge policy:

- Direct KV transfer is used only when safe.
- If compatibility is poor, Mind Meld replays missing suffix tokens to rebuild cache.
- KV cache translation is experimental and requires explicit opt-in (`--allow-kv-cache-translation`).
- `--force-kv-cache-translation` bypasses safety checks and can degrade quality.

Useful diagnostics flags:

- `--meld-diagnostics`
- `--use-stats-tracker --stats-file meld.json`
- `--summary-only`
- `--no-step-delay`

## Recommended Patterns

1. Identical model + different personas for stable multi-perspective output.
2. Same-family model pairs for best KV compatibility.
3. Small+large model pair for speculative decoding speed/quality tradeoff.
4. Use `--order-neutral` or `--soft-swap` when swap-order sensitivity appears.

## Implementation Pointers

- Blending: `src/mind_meld/core/blending.py`
- ABE: `src/mind_meld/core/abe_ensemble.py`
- State bridging: `src/mind_meld/bridges/state_bridge.py`
- Advanced routing/decoding: `src/mind_meld/advanced/`
- Isolated cross-model KV proof harness: `src/mind_meld/latent_handoff/README.md`
