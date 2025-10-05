# Models Directory

This directory is for storing or linking to local model files (GGUF, ONNX, etc.).

## Purpose

The `models/` directory serves as a central location for:
- Storing downloaded model files
- Creating symlinks to models stored elsewhere (e.g., Ollama models)
- Organizing local model files for easy reference

## Model Search Path Priority

When you specify a model file (e.g., `model.gguf`), the system searches in this order:

1. **Project models directory**: `gamma/models/` (this directory)
2. **Ollama system directory**: `/usr/share/ollama/.ollama/models`
3. **Ollama user directory**: `~/.ollama/models`
4. **HuggingFace cache**: `~/.cache/huggingface/hub`

For HuggingFace models (e.g., `google/gemma-3-1b-it`), the identifier is passed directly to the transformers library.

## Setting Up Symlinks to Ollama Models

If you have models managed by Ollama, you can create symlinks instead of duplicating files:

### Find Your Ollama Model

Ollama stores models in blob directories. To find a specific model:

```bash
# List all Ollama models
ls -lh /usr/share/ollama/.ollama/models/blobs/

# Or in user directory
ls -lh ~/.ollama/models/blobs/
```

### Create a Symlink

**Option 1: Manual symlink creation**

```bash
# Link to a specific Ollama model blob
ln -s /usr/share/ollama/.ollama/models/blobs/sha256-abc123... models/my-model.gguf

# Or from user directory
ln -s ~/.ollama/models/blobs/sha256-xyz789... models/another-model.gguf
```

**Option 2: Using the helper script (coming soon)**

```python
from src.core.model_paths import create_model_symlink

# Create a symlink
create_model_symlink(
    target_path="/usr/share/ollama/.ollama/models/blobs/sha256-abc123...",
    link_name="my-model.gguf"
)
```

### Finding Ollama Model Blob Names

Ollama doesn't use human-readable filenames. To find the blob for a specific model:

```bash
# List models in Ollama
ollama list

# Show model details
ollama show <model-name> --modelfile

# The blob file is typically in:
# /usr/share/ollama/.ollama/models/blobs/sha256-<hash>
# or
# ~/.ollama/models/blobs/sha256-<hash>
```

**Tip**: Look at file sizes to identify which blob corresponds to your model:

```bash
# Show sizes
ls -lh /usr/share/ollama/.ollama/models/blobs/ | grep -E "G|M"

# Sort by size
ls -lhS /usr/share/ollama/.ollama/models/blobs/
```

## Example Directory Structure

After setting up symlinks, your models directory might look like:

```
models/
├── README.md                    # This file
├── gemma-3-27b.gguf            # Symlink → /usr/share/ollama/.ollama/models/blobs/sha256-...
├── llama3-8b.gguf              # Symlink → ~/.ollama/models/blobs/sha256-...
└── my-custom-model.gguf        # Actual file
```

## Using Models

### With LlamaCpp Engine

```bash
# By filename (searches all paths)
python game.py --engine llamacpp --model gemma-3-27b.gguf

# By full path (if not in search paths)
python game.py --engine llamacpp --model /path/to/model.gguf
```

### With ONNX Engine

```bash
python game.py --engine onnx --model my-model.onnx --onnx-tokenizer google/gemma-3-1b-it
```

### With Mind Meld

```bash
python tools/run_mind_meld_cli.py \
  --models llamacpp:gemma-3-27b.gguf llamacpp:llama3-8b.gguf \
  --strategy pattern
```

## Listing Available Models

You can see all models found in the search paths:

```python
from src.core.model_paths import list_available_models

models = list_available_models()
for location, model_list in models.items():
    print(f"\n{location}:")
    for model in model_list:
        print(f"  - {model['filename']} ({model['size_mb']:.1f} MB)")
```

## Permissions

If you're linking to Ollama system models (`/usr/share/ollama/`), you may need appropriate read permissions:

```bash
# Check permissions
ls -la /usr/share/ollama/.ollama/models/blobs/

# If needed, add your user to the ollama group (if it exists)
sudo usermod -a -G ollama $USER
```

## Troubleshooting

**Model not found**: If the system can't find your model:
1. Check the filename matches exactly
2. Verify the file exists: `ls -la models/`
3. For symlinks, verify target exists: `ls -la $(readlink models/your-model.gguf)`
4. Check file permissions

**Broken symlinks**: Remove and recreate:
```bash
rm models/broken-link.gguf
ln -s /correct/path/to/model models/model.gguf
```

## Git Ignore

This directory is configured in `.gitignore` to exclude model files but include this README:

```gitignore
models/*
!models/README.md
```

This prevents accidentally committing large model files to version control.
