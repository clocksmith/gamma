# Color Utilities (dream.js)

This module contains the **dream.js** color utility library, originally from the DREAM project.

## What is dream.js?

A production-ready JavaScript library for dynamic color theming, forked from Google's material-color-utilities.

**Features:**
- Material Design 3 color schemes
- HCT (Hue, Chroma, Tone) color space
- Perceptually uniform color manipulation
- Multi-seed theme generation
- Zero dependencies

## Usage

```javascript
import { Hct, themeFromSourceColor } from './dream.js';

// Generate Material Design palette
const theme = themeFromSourceColor(0x0000ff); // Blue

// Use HCT for perceptually uniform colors
const color = Hct.fromInt(0xff0000);
color.hue = 120; // Shift to green while preserving appearance
```

## MILCHICK Demo

The `demo/` directory contains an interactive demo showcasing agentic AI for color selection:
- Natural language color prompts ("sunset vibes", "corporate professional")
- Image-based color extraction
- Iterative refinement with AI feedback
- Deterministic results for reproducibility

## Testing

See `test/` directory for examples and unit tests.

## Integration with GAMMA

dream.js is used in GAMMA's language comparison benchmarks to test:
- How well LLMs can integrate with real-world libraries
- TypeScript vs JavaScript performance on complex color tasks
- Agentic AI capabilities for creative color selection

## License

Apache 2.0 (inherited from Google's material-color-utilities)
