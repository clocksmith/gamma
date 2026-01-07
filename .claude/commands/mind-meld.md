---
description: Run Mind Meld multi-model generation
allowed-tools: Bash
argument-hint: [--preset NAME | MODEL MODEL] [--blend MODE] [--prompt TEXT]
---

Run Mind Meld with the specified models and options.

## Quick Examples

```bash
# Use a preset
/mind-meld --preset creative
/mind-meld --preset debate --prompt "Is AI beneficial?"

# Model aliases (shorter than full paths)
/mind-meld gemma-1b gemma-2b --blend dynamic
/mind-meld gemma-1b@Optimist gemma-2b@Skeptic

# Full model specs
/mind-meld pytorch:google/gemma-3-1b-it pytorch:google/gemma-2-2b-it

# Load a config file
/mind-meld configs/mind_meld/example-custom.yaml
```

## Available Presets

- `creative` - Smooth blending, storytelling personas
- `analytical` - Logical analysis, confidence-based swaps
- `debate` - Opposing viewpoints, hard switching
- `brainstorm` - 3 models, random swaps, idea generation
- `experimental` - All advanced features enabled
- `minimal` - Simple round-robin

## Model Aliases

- `gemma-1b` -> pytorch:google/gemma-3-1b-it
- `gemma-2b` -> pytorch:google/gemma-2-2b-it
- `gemma-4b` -> pytorch:google/gemma-3-4b-it
- `phi-mini` -> pytorch:microsoft/Phi-3.5-mini-instruct

## Blend Modes

- `--blend hard` - No blending, pure switching
- `--blend soft` - Gentle blending
- `--blend dynamic` - Adaptive based on confidence
- `--blend smooth` - Maximum interpolation
- `--blend 70` - Numeric strength (0-100)

## Utility Commands

```bash
/mind-meld --list-presets   # Show available presets
/mind-meld --list-aliases   # Show model shortcuts
/mind-meld --list-models    # Show available models
/mind-meld gemma-1b gemma-2b --show-config  # Preview config
/mind-meld gemma-1b gemma-2b --save-config my-setup.yaml  # Save for reuse
```

```bash
python3 tools/run_mind_meld_cli.py $ARGUMENTS
```
