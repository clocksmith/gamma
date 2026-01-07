# Mind Meld Configuration

This directory contains YAML configuration files for Mind Meld.

## Quick Start

```bash
# Use a preset
python tools/run_mind_meld_cli.py --preset creative

# Use a config file directly
python tools/run_mind_meld_cli.py configs/mind_meld/example-custom.yaml

# Override config values with CLI flags
python tools/run_mind_meld_cli.py --preset debate --steps 100 --temperature 0.5
```

## Directory Structure

```
configs/mind_meld/
  presets/           # Built-in preset configurations
    creative.yaml    # Creative writing with smooth blending
    analytical.yaml  # Logical analysis with confidence-based swaps
    debate.yaml      # Opposing personas taking turns
    brainstorm.yaml  # Multi-model idea generation
    experimental.yaml # All advanced features enabled
    minimal.yaml     # Simple round-robin switching
  example-custom.yaml # Template for custom configs
  README.md          # This file
```

## User Configuration

Create `~/.mind-meld.yaml` to define personal aliases:

```yaml
aliases:
  fast: "pytorch:google/gemma-3-1b-it"
  smart: "pytorch:google/gemma-3-4b-it"
  local: "llamacpp:/path/to/model.gguf"
```

Then use them:
```bash
python tools/run_mind_meld_cli.py fast smart --blend dynamic
```

## CLI Shortcuts

```bash
# Model aliases (built-in)
gemma-1b, gemma-2b, gemma-4b, phi-mini, mistral-7b

# Persona binding
gemma-1b@Optimist gemma-2b@Skeptic

# Blend modes
--blend hard     # No blending
--blend soft     # Gentle blending
--blend dynamic  # Adaptive
--blend smooth   # Maximum interpolation
--blend 70       # Numeric strength (0-100)

# Output formats
--output json
--output markdown
```

## Configuration Priority

1. CLI flags (highest priority)
2. Config file (--config or positional .yaml)
3. Preset (--preset)
4. Defaults (lowest priority)

This means you can start with a preset and override specific values:
```bash
python tools/run_mind_meld_cli.py --preset creative --temperature 0.5 --steps 100
```
