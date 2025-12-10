# Web GAMMA

**[Play Now](https://simulatte.world)**

> **Note**: This web app is deployed from [github.com/clocksmith/simulatte](https://github.com/clocksmith/simulatte). The source in this directory is the development copy.

A browser-based game where you guess the next token an LLM will generate.

## Features

- Token prediction with multiple choice options
- Probability visualization showing top predictions after guessing
- Attention heatmap showing token influence (when model supports it)
- Multiple model options from small (135M) to experimental (3B)

## Tech Stack

- **Inference**: Transformers.js with WebGPU/WASM
- **Build**: Vite
- **Hosting**: Firebase

## Models

Small models work on most devices. Experimental models may fail on some hardware.

## Development

```bash
npm install
npm run dev
```

## Deploy

```bash
npm run build && firebase deploy
```

## License

MIT
