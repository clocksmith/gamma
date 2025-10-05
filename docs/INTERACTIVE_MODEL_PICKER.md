# Interactive Model Picker

The interactive model picker shows you which models are available locally versus which can be downloaded from HuggingFace.

## Features

### Visual Indicators

- **💾 Local**: Model is available on disk (ready to use immediately)
- **☁️ Download**: Model will be downloaded from HuggingFace on first use
- **⭐ Recommended**: Recommended for new users
- **🔐 Auth Required**: Requires HuggingFace authentication

### Model Sources

The picker shows models from:

1. **Local files** in `models/` directory
2. **Ollama models** (via symlinks from `/usr/share/ollama/.ollama/models`)
3. **User Ollama models** (from `~/.ollama/models`)
4. **HuggingFace catalog** (downloadable models)

### Navigation

When selecting a model, you can:

- **Enter number**: Select model by number
- **n**: Next page
- **p**: Previous page
- **s**: Search/filter models
- **c**: Enter custom model path
- **r**: Show only recommended models
- **l**: Show only local models (already downloaded)
- **a**: Show all models
- **q**: Cancel selection

## Example Session

```
📦 Available Models (Page 1/2):
--------------------------------------------------------------------------------
💾 ⭐  1. test-ollama-model.gguf                   [  ?] 16.9GB
          Local GGUF - /home/user/gamma/models
          ✓ Local: ...ollama/models/blobs/...

☁️     2. gemma-2b-it-q4_k_m.gguf                  [ 2B]   ~2GB
          Gemma 2B Instruct - 4-bit quantized GGUF
          ☁️  Download: HuggingFace (auto-download)

☁️     3. gemma-2b-it-q5_k_m.gguf                  [ 2B] ~2.5GB
          Gemma 2B Instruct - 5-bit quantized GGUF
          ☁️  Download: HuggingFace (auto-download)

--------------------------------------------------------------------------------

Legend: 💾=Local  ☁️=Download  ⭐=Recommended  🔐=Auth Required
Status: 1 local, 4 downloadable

Options:
  • Enter model number (1-5)
  • 'n' - Next page
  • 'p' - Previous page
  • 's' - Search/filter models
  • 'c' - Enter custom model path
  • 'r' - Show only recommended models
  • 'l' - Show only local models
  • 'a' - Show all models
  • 'q' - Cancel selection

Your choice: l
Showing 1 local models.

📦 Available Models (Page 1/1):
--------------------------------------------------------------------------------
💾 ⭐  1. test-ollama-model.gguf                   [  ?] 16.9GB
          Local GGUF - /home/user/gamma/models
          ✓ Local: ...ollama/models/blobs/...
--------------------------------------------------------------------------------

Your choice: 1

✓ Selected: test-ollama-model.gguf
```

## Setting Up Local Models

### From Ollama

```bash
# Find Ollama models
ls -lhS /usr/share/ollama/.ollama/models/blobs/

# Create symlink
ln -s /usr/share/ollama/.ollama/models/blobs/sha256-abc123... \
      models/llama3-8b.gguf

# Model will now appear in picker with 💾 indicator
```

### Download Directly

```bash
# Download GGUF from HuggingFace
python tools/download_model.py \
  --repo-id google/gemma-3-27b-it-qat-q4_0-gguf \
  --filename gemma-3-27b-it-Q4_0.gguf

# File saved to models/ and will appear with 💾 indicator
```

## Benefits

1. **See what's local**: Quickly identify models that won't require download
2. **Estimate sizes**: Know download size before selecting
3. **Discover Ollama models**: Automatically finds models from Ollama
4. **Filter options**: Show only local or recommended models
5. **Custom paths**: Still supports entering custom paths

## Technical Details

- Local model discovery runs when picker opens
- Scans all paths in `src.core.model_paths.DEFAULT_MODEL_SEARCH_PATHS`
- For GGUF: searches for `.gguf` files when using `llamacpp` engine
- For ONNX: searches for `.onnx` files when using `onnx` engine
- Symlinks are followed and shown with abbreviated paths
- File sizes are computed from actual files on disk

See also: [Model Setup Guide](MODEL_SETUP.md)
