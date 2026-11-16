## Flux Web Interface

Browser-based interface for Flux diffusion learning lab.

### Status

**Frontend**: ✅ Complete - Beautiful, responsive UI with interactive controls
**Backend**: 🚧 Future work - Requires API server implementation

### Current Implementation

The web interface (`index.html`) is a fully functional frontend demo that shows:

- Interactive parameter controls (guidance scale, steps, seed)
- Real-time slider feedback
- Responsive design
- Loading states and error handling
- Educational explanations for each parameter

### What's Needed for Full Functionality

To enable actual image generation in the browser, you need:

#### Option 1: Python Backend API (Recommended)

Create a FastAPI/Flask server that wraps Flux:

```python
# api_server.py (to be implemented)
from fastapi import FastAPI
from flux.engines import DiffusersEngine
from flux.engines.base import DiffusionConfig

app = FastAPI()
engine = None

@app.on_event("startup")
async def startup():
    global engine
    config = DiffusionConfig(model_name="stabilityai/stable-diffusion-2-1-base")
    engine = DiffusersEngine(config)
    engine.load()

@app.post("/generate")
async def generate(request: dict):
    output = engine.generate(
        prompt=request["prompt"],
        negative_prompt=request.get("negative_prompt"),
        num_inference_steps=request.get("steps", 50),
        guidance_scale=request.get("guidance", 7.5),
        seed=request.get("seed"),
    )

    # Convert PIL image to base64
    import io
    import base64
    buffer = io.BytesIO()
    output.image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return {
        "image": f"data:image/png;base64,{img_str}",
        "metadata": output.metadata
    }

# Run with: uvicorn api_server:app --reload
```

Then update `index.html` to call this API:

```javascript
async function generate() {
    const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            prompt: prompt,
            negative_prompt: negativePrompt,
            steps: parseInt(steps),
            guidance: parseFloat(guidance),
            seed: seed ? parseInt(seed) : null
        })
    });

    const data = await response.json();
    // Display data.image
}
```

#### Option 2: ONNX Runtime Web (Client-Side)

Use ONNX Runtime Web to run models directly in the browser:

1. Export Stable Diffusion to ONNX format
2. Load with ONNX Runtime Web
3. Run inference using WebGPU/WASM
4. Display results directly

**Pros**: No backend needed, runs locally
**Cons**: Large model files, slower, limited browser compatibility

#### Option 3: Transformers.js (Experimental)

Use Hugging Face's Transformers.js for client-side inference:

```javascript
import { pipeline } from '@xenova/transformers';

const pipe = await pipeline('text-to-image', 'stabilityai/stable-diffusion-2-1-base');
const image = await pipe(prompt);
```

**Pros**: Simple API, no backend
**Cons**: Experimental, limited model support, slower

### Usage (Current Frontend Demo)

1. Open `index.html` in a browser
2. Enter a prompt and adjust parameters
3. Click "Generate Image"
4. See demo loading state (no actual generation yet)

### Development Roadmap

**Phase 1** (Current): ✅
- Frontend UI design
- Interactive controls
- Responsive layout

**Phase 2** (Next):
- Backend API server
- Image generation endpoint
- WebSocket for progress updates

**Phase 3** (Future):
- Real-time preview during generation
- Gallery of generated images
- Session history
- Parameter presets

**Phase 4** (Advanced):
- Multi-model comparison view
- Attention visualization overlay
- Latent space explorer
- Learning games (web version)

### Files

- `index.html` - Main web interface (standalone)
- `README.md` - This file
- `package.json` - To be added for npm dependencies
- `api_server.py` - To be implemented

### Running

**Current (Demo)**:
```bash
# Just open in browser
open index.html
# or
python -m http.server 8000
# Then visit http://localhost:8000
```

**Future (With Backend)**:
```bash
# Terminal 1: Start API server
uvicorn api_server:app --reload

# Terminal 2: Serve frontend
python -m http.server 8000

# Visit http://localhost:8000
```

### Design Notes

The interface is designed to be:
- **Educational**: Clear explanations for each parameter
- **Intuitive**: Sliders with real-time feedback
- **Beautiful**: Modern gradient design matching Flux branding
- **Accessible**: Works on desktop and mobile

### Integration with Flux CLI

The web interface complements the CLI:

- **CLI**: Best for learning games, deep inspection, experimentation
- **Web**: Best for quick generation, sharing, accessibility

Both share the same Flux backend and gamma-core infrastructure.

### Contributing

To implement backend support:

1. Create `api_server.py` with FastAPI
2. Add CORS support for local development
3. Implement `/generate` endpoint
4. Add WebSocket for progress streaming
5. Update `index.html` to use real API
6. Add error handling and validation

See `../README.md` for Flux architecture and CLI context.
