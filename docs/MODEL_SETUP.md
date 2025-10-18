# Model Setup Guide

This guide explains how to set up and manage models for use with Gamma, including integration with Ollama models.

## Table of Contents

- [Overview](#overview)
- [Model Storage Locations](#model-storage-locations)
- [Quick Start](#quick-start)
- [Working with Ollama Models](#working-with-ollama-models)
- [Downloading Models](#downloading-models)
- [Model Path Resolution](#model-path-resolution)
- [Troubleshooting](#troubleshooting)

---

## Overview

Gamma supports multiple model formats and sources:
- **HuggingFace models**: Downloaded automatically via transformers library
- **GGUF models**: For llama.cpp engine (quantized models)
- **ONNX models**: For ONNX Runtime engine
- **Ollama models**: Reuse models managed by Ollama

---

## Model Storage Locations

### Search Path Priority

When you specify a model file (e.g., `model.gguf`), Gamma searches in this order:

1. **Project models directory**: `gamma/models/`
2. **Ollama system directory**: `/usr/share/ollama/.ollama/models`
3. **Ollama user directory**: `~/.ollama/models`
4. **HuggingFace cache**: `~/.cache/huggingface/hub`

### Model Types

| Type | Example | Engine | Storage |
|------|---------|--------|---------|
| HuggingFace | `google/gemma-3-1b-it` | pytorch, tensorflow, jax, mlx | Auto-downloaded to `~/.cache/huggingface/hub` |
| GGUF | `model.gguf` | llamacpp | Local or Ollama |
| ONNX | `model.onnx` | onnx | Local |

---

## Quick Start

### Option 1: Use HuggingFace Models (Easiest)

```bash
# Models are downloaded automatically
python gamma.py game --engine pytorch --model google/gemma-3-1b-it
```

### Option 2: Use Local GGUF Files

```bash
# Download a GGUF model
python tools/download_model.py \
  --repo-id google/gemma-3-27b-it-qat-q4_0-gguf \
  --filename gemma-3-27b-it-Q4_0.gguf

# Use it (file is saved to gamma/models/)
python gamma.py game --engine llamacpp --model gemma-3-27b-it-Q4_0.gguf
```

### Option 3: Link Ollama Models

```bash
# Create symlink to Ollama model
ln -s /usr/share/ollama/.ollama/models/blobs/sha256-abc123... \
      models/my-model.gguf

# Use it
python gamma.py game --engine llamacpp --model my-model.gguf
```

---

## Working with Ollama Models

Ollama manages models efficiently, and Gamma can reuse them without duplication.

### Step 1: Find Your Ollama Model

Ollama stores models as blobs with SHA256 hashes. To find a model:

```bash
# List all Ollama models
ollama list

# Show model details
ollama show llama3:8b

# Find the blob file (system-wide)
ls -lhS /usr/share/ollama/.ollama/models/blobs/

# Or in user directory
ls -lhS ~/.ollama/models/blobs/
```

**Tip**: Match file sizes from `ollama show` to identify the correct blob.

### Step 2: Create a Symlink

#### Manual Method

```bash
# Navigate to your gamma directory
cd /path/to/gamma

# Create symlink with a friendly name
ln -s /usr/share/ollama/.ollama/models/blobs/sha256-1234567890abcdef... \
      models/llama3-8b.gguf

# Verify the link
ls -lh models/llama3-8b.gguf
```

#### Python Helper Method

```python
from src.core.model_paths import create_model_symlink

# Create symlink
create_model_symlink(
    target_path="/usr/share/ollama/.ollama/models/blobs/sha256-abc...",
    link_name="llama3-8b.gguf"
)
```

### Step 3: Use the Model

```bash
# Single model usage
python gamma.py game --engine llamacpp --model llama3-8b.gguf

# Mind Meld with multiple models
python tools/run_mind_meld_cli.py \
  --models llamacpp:llama3-8b.gguf llamacpp:gemma-3-27b.gguf \
  --strategy pattern
```

### Finding Specific Ollama Models

Ollama stores metadata in manifest files. To map model names to blobs:

```bash
# Check manifests directory
ls /usr/share/ollama/.ollama/models/manifests/

# Example: registry.ollama.ai/library/llama3/
# Contains version tags that reference blobs

# The actual model weights are in blobs/sha256-*
# Match by file size to identify the right one
```

**Example workflow**:

1. Run `ollama show llama3:8b` → Note the size (e.g., 4.7GB)
2. Run `ls -lhS /usr/share/ollama/.ollama/models/blobs/` → Find file ~4.7GB
3. Create symlink to that blob

---

## Downloading Models

### GGUF Models from HuggingFace

Use the download utility:

```bash
python tools/download_model.py \
  --repo-id google/gemma-3-27b-it-qat-q4_0-gguf \
  --filename gemma-3-27b-it-Q4_0.gguf
```

This downloads to `gamma/models/`.

### HuggingFace Transformer Models

No manual download needed:

```bash
# First run will download and cache
python gamma.py game --engine pytorch --model google/gemma-3-1b-it
```

Models are cached in `~/.cache/huggingface/hub/`.

### Gated Models

For gated models (require HuggingFace approval):

```bash
# Login to HuggingFace
huggingface-cli login

# Or use token directly
python gamma.py game --engine pytorch --model google/gemma-3-1b-it --hf-token YOUR_TOKEN
```

---

## Model Path Resolution

The `resolve_model_path()` function automatically finds models:

### How It Works

```python
from src.core.model_paths import resolve_model_path

# HuggingFace models → returned as-is
resolve_model_path("google/gemma-3-1b-it")
# → "google/gemma-3-1b-it"

# Local files → searches paths
resolve_model_path("model.gguf")
# → "/home/user/gamma/models/model.gguf"

# Absolute paths → validated and returned
resolve_model_path("/absolute/path/to/model.gguf")
# → "/absolute/path/to/model.gguf"

# Ollama models → found via search
resolve_model_path("llama3-8b.gguf")
# → "/usr/share/ollama/.ollama/models/blobs/sha256-..."
```

### Custom Search Paths

```python
from src.core.model_paths import resolve_model_path

# Add custom paths
custom_path = resolve_model_path(
    "model.gguf",
    additional_paths=["/mnt/external/models"]
)
```

### List Available Models

```python
from src.core.model_paths import list_available_models

models = list_available_models()
for location, model_list in models.items():
    print(f"\n{location}:")
    for model in model_list:
        print(f"  - {model['filename']} ({model['size_mb']:.1f} MB)")
```

---

## Troubleshooting

### Model Not Found

**Problem**: `FileNotFoundError` or "Model not found"

**Solutions**:
1. Check the filename: `ls models/`
2. Verify search paths are accessible
3. For Ollama models, ensure permissions:
   ```bash
   # Check permissions
   ls -la /usr/share/ollama/.ollama/models/blobs/

   # Add yourself to ollama group if it exists
   sudo usermod -a -G ollama $USER
   # Then logout and login
   ```

### Broken Symlinks

**Problem**: Symlink points to non-existent file

**Solution**:
```bash
# Check symlink target
readlink models/my-model.gguf

# Verify target exists
ls -la $(readlink models/my-model.gguf)

# Fix broken link
rm models/my-model.gguf
ln -s /correct/path models/my-model.gguf
```

### Permission Denied

**Problem**: Cannot read Ollama model files

**Solutions**:

```bash
# Option 1: Change permissions (if you own the files)
sudo chmod 644 /usr/share/ollama/.ollama/models/blobs/sha256-*

# Option 2: Add user to ollama group
sudo usermod -a -G ollama $USER
newgrp ollama  # or logout/login

# Option 3: Copy to user directory instead of linking
cp /usr/share/ollama/.ollama/models/blobs/sha256-abc... \
   ~/.ollama/models/my-model.gguf
```

### HuggingFace Cache Issues

**Problem**: Models re-downloading or cache corruption

**Solutions**:
```bash
# Clear cache
rm -rf ~/.cache/huggingface/hub/*

# Or set custom cache location
export HF_HOME=/mnt/large-drive/huggingface

# Then re-download
python gamma.py game --engine pytorch --model google/gemma-3-1b-it
```

### Out of Disk Space

**Problem**: Not enough space for model downloads

**Solutions**:
1. Use quantized GGUF models (smaller)
2. Symlink to external drive
3. Set custom cache:
   ```bash
   export HF_HOME=/mnt/external/hf-cache
   ```

---

## Advanced: Model Organization

### Organizing Multiple Models

```
gamma/models/
├── README.md
├── gemma/
│   ├── gemma-3-1b.gguf      → symlink to Ollama
│   ├── gemma-3-27b.gguf     → symlink to Ollama
│   └── gemma-3-4b-q4.gguf   → actual file
├── llama/
│   ├── llama3-8b.gguf       → symlink
│   └── llama3-70b.gguf      → symlink
└── custom/
    └── my-fine-tuned.gguf   → actual file
```

Reference models with subdirectories:

```bash
python gamma.py game --engine llamacpp --model gemma/gemma-3-27b.gguf
```

### Batch Symlink Creation

```bash
#!/bin/bash
# Create symlinks for all Ollama models

OLLAMA_BLOBS="/usr/share/ollama/.ollama/models/blobs"
GAMMA_MODELS="./models"

for blob in $OLLAMA_BLOBS/sha256-*; do
    size=$(stat -f%z "$blob" 2>/dev/null || stat -c%s "$blob")
    # Only link files > 1GB (likely model weights)
    if [ $size -gt 1000000000 ]; then
        hash=$(basename "$blob" | cut -d'-' -f2 | cut -c1-8)
        ln -s "$blob" "$GAMMA_MODELS/ollama-$hash.gguf"
        echo "Linked: ollama-$hash.gguf ($(numfmt --to=iec $size))"
    fi
done
```

---

## Summary

- **HuggingFace models**: Just use the identifier (e.g., `google/gemma-3-1b-it`)
- **Local GGUF**: Download to `models/` or symlink from Ollama
- **Ollama integration**: Create symlinks to `/usr/share/ollama/.ollama/models/blobs/`
- **Path resolution**: Automatic search across multiple locations

For more details, see:
- `models/README.md` - Models directory documentation
- `src/core/model_paths.py` - Path resolution implementation
- `tools/download_model.py` - Model download utility
