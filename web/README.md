# Web GAMMA

**[Play Now](https://gamma-web-game.web.app)**

A browser-based game where you guess the next token an LLM will generate.

## Features

- Token prediction with multiple choice options
- Probability visualization showing top predictions after guessing
- Attention heatmap showing token influence (when model supports it)
- Multiple model options from small (135M) to experimental (3B)

## Tech Stack

- **Inference**: Transformers.js with WebGPU/WASM
- **Build**: None (static ES modules served directly)
- **Hosting**: Firebase

## Source of Truth

- Edit files directly in `web/`
- Do not commit generated bundles under `web/dist/`

## Models

Small models work on most devices. Experimental models may fail on some hardware.

## Development (static only)

```bash
cd gamma/web
python3 -m http.server 5173
```

## Deploy

```bash
firebase deploy
```

The generated M3T4 2038 review index is published under `/m3t4-2038/`.
Build and deploy it from `games/frontier-2038`:

```bash
npm run publish:firebase:deploy
```

The generated directory is ignored by Git. `robots.txt`, HTML metadata, and
path-scoped `X-Robots-Tag` headers ask cooperative search and AI crawlers not
to index, archive, or reuse it. These directives are not access control and
cannot prevent a hostile scraper from requesting a public URL.

## License

MIT
