# Web GAMMA

**[Play Now](https://gamma-web-game.web.app)**

A browser-based port of the GAMMA token prediction game.

## Overview

Web GAMMA is an educational game that teaches how Large Language Models work through interactive token prediction. Players guess which token the LLM will generate next, learning about:

- Token probabilities and sampling strategies
- Attention mechanisms and context understanding
- Temperature, top-k, and top-p filtering
- Multi-model collaboration (Mind Meld)

## Features

### Core Game
- Token prediction with multiple choice options
- Real-time probability visualization across all sampling stages
- Attention heatmap showing which tokens influence predictions
- Score tracking, streaks, and achievements
- Progressive difficulty system

### Mind Meld (Multi-Model)
- Run multiple models simultaneously
- Swap strategies: fixed interval, pattern-based, confidence, perplexity
- Logit blending and Agreement-Based Ensembling (ABE)
- Vocabulary translation between different model architectures

### Visual Design
- Reploid cyberpunk theme (cyan/magenta neon colors)
- Scanline overlay and glow effects
- Smooth animations and transitions
- Mobile responsive layout

## Tech Stack

- **Inference**: Transformers.js (primary), WebLLM (fallback)
- **Models**: Qwen 2.5 (0.5B-2B), SmolLM2, Gemma 2
- **Storage**: IndexedDB for sessions and settings
- **Styling**: CSS variables extending reploid theme

## Supported Models

| Model | Size | VRAM | Notes |
|-------|------|------|-------|
| Qwen/Qwen2.5-0.5B-Instruct | 500M | 600MB | Recommended for quick start |
| HuggingFaceTB/SmolLM2-360M-Instruct | 360M | 400MB | Lightweight option |
| Qwen/Qwen2.5-1.5B-Instruct | 1.5B | 1.8GB | Balanced performance |
| google/gemma-2-2b-it | 2B | 2.5GB | Higher quality |

## Quick Start

```bash
# Serve the web directory
npx serve .

# Or use any static file server
python -m http.server 8000
```

Then open `http://localhost:8000` in a WebGPU-capable browser (Chrome 113+, Edge 113+).

## Project Structure

See [PLAN.md](./PLAN.md) for the complete implementation plan and file structure.

## References

- Original GAMMA: `/home/clocksmith/deco/gamma/`
- Reploid UI: `/home/clocksmith/deco/reploid/`
- Transformers.js: https://huggingface.co/docs/transformers.js
- WebLLM: https://webllm.mlc.ai/

## License

MIT
