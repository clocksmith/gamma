# Natural Language to GAMMA Commands

GAMMA’s CLI is the source of truth. If you want to go from “what I want” to “what to run”, use an LLM as a translator, but keep it constrained:
- output a single command you can run
- use only real GAMMA flags (verify with `--help`)
- keep commands reproducible and reviewable

## Quick Prompt (copy/paste into any LLM)

> You are a CLI translator for the GAMMA project. Convert my request into a single `python gamma.py ...` command (or `python tools/...` when appropriate). Do not invent flags. If unsure, output a `--help` command instead of guessing. Prefer explicit flags for reproducibility (engine, model, temperature, top-k, top-p, steps). If the request needs logits (game probabilities, comparison, mind-meld), avoid engines that can’t provide logits.

If you use Codex, the same guidance exists as a skill named `gamma-nl-cli`.

## Verification Commands

```bash
python gamma.py help
python gamma.py game --help
python gamma.py help select
python gamma.py list
python gamma.py select --validate pytorch:google/gemma-2-2b-it
```

## Examples

```bash
# "I want to play with Gemma 2B using temperature 0.9"
python gamma.py game --engine pytorch --model google/gemma-2-2b-it --temperature 0.9
```

```bash
# "Compare Qwen and DeepSeek on a coding prompt"
python gamma.py game --comparison \
  --comparison-models \
    ollama:qwen3-coder:30b \
    ollama:deepseek-r1:32b \
  --prompt "Write a Python function to calculate fibonacci"
```

```bash
# "Meld Gemma models with dynamic blending"
python gamma.py mind-meld gemma-1b gemma-2b --blend dynamic
```

