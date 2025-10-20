#!/usr/bin/env python3
"""
List available models from all sources.

Discovers models from:
- Ollama (via API or CLI)
- HuggingFace cache
- Local GGUF files
- Project models directory
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def list_ollama_models():
    """List models from Ollama."""
    print("=" * 70)
    print("📦 Ollama Models")
    print("=" * 70)

    try:
        # Try Ollama CLI first
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')

            if len(lines) <= 1:
                print("  (No models found)")
                return

            # Parse header and models
            header = lines[0]
            models = lines[1:]

            print(f"\n  {'Model':<35} {'Size':<12} {'Modified':<20}")
            print("  " + "-" * 67)

            for line in models:
                parts = line.split()
                if len(parts) >= 3:
                    model_name = parts[0]
                    model_id = parts[1] if len(parts) > 1 else ""
                    size = parts[2] if len(parts) > 2 else "N/A"
                    modified = " ".join(parts[3:]) if len(parts) > 3 else "N/A"

                    print(f"  {model_name:<35} {size:<12} {modified:<20}")

            print(f"\n  Total: {len(models)} model(s)")
            print(f"\n  💡 Use as: ollama:MODEL_NAME (e.g., ollama:gemma2:2b)")
        else:
            print("  ⚠️  Ollama CLI not responding")
            print("  Is Ollama running? Try: ollama serve")

    except FileNotFoundError:
        print("  ⚠️  Ollama not installed")
        print("  Install from: https://ollama.ai/")
    except subprocess.TimeoutExpired:
        print("  ⚠️  Ollama timeout")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")

    print()


def list_huggingface_models():
    """List models from HuggingFace cache."""
    print("=" * 70)
    print("🤗 HuggingFace Cached Models")
    print("=" * 70)

    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"

    if not hf_cache.exists():
        print("  (Cache directory not found)")
        print(f"  Expected at: {hf_cache}")
        print()
        return

    # Find model directories
    model_dirs = [d for d in hf_cache.iterdir() if d.is_dir() and d.name.startswith('models--')]

    if not model_dirs:
        print("  (No cached models)")
        print("  Models will be auto-downloaded on first use")
        print()
        return

    print(f"\n  {'Model':<50} {'Size (GB)':<12}")
    print("  " + "-" * 62)

    for model_dir in sorted(model_dirs):
        # Parse model name from directory (models--org__model -> org/model)
        model_name = model_dir.name.replace('models--', '').replace('__', '/')

        # Calculate total size
        total_size = 0
        try:
            for item in model_dir.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            size_gb = total_size / (1024**3)
            print(f"  {model_name:<50} {size_gb:>8.2f} GB")
        except Exception:
            print(f"  {model_name:<50} {'ERROR':<12}")

    print(f"\n  Total: {len(model_dirs)} model(s)")
    print(f"  Cache location: {hf_cache}")
    print(f"\n  💡 Use as: pytorch:ORG/MODEL (e.g., pytorch:google/gemma-2-2b-it)")
    print()


def list_local_gguf_files():
    """List local GGUF files in common locations."""
    print("=" * 70)
    print("📁 Local GGUF Files")
    print("=" * 70)

    # Search locations
    project_root = Path(__file__).parent.parent
    search_paths = [
        project_root / "models",
        Path.home() / ".ollama" / "models" / "blobs",
        Path("/usr/share/ollama/.ollama/models/blobs"),
    ]

    found_any = False

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # Find GGUF files
        gguf_files = list(search_path.rglob("*.gguf"))

        if gguf_files:
            if not found_any:
                print(f"\n  {'Location':<30} {'File':<35} {'Size (GB)':<12}")
                print("  " + "-" * 77)
                found_any = True

            for gguf_file in sorted(gguf_files):
                size_gb = gguf_file.stat().st_size / (1024**3)
                location = str(search_path.name)[:28]
                filename = gguf_file.name[:33]
                print(f"  {location:<30} {filename:<35} {size_gb:>8.2f} GB")

    if not found_any:
        print("  (No GGUF files found)")
        print("\n  Searched in:")
        for path in search_paths:
            exists = "✓" if path.exists() else "✗"
            print(f"    {exists} {path}")
        print("\n  💡 Place GGUF files in: " + str(project_root / "models"))
    else:
        print(f"\n  💡 Use as: llamacpp:/path/to/file.gguf")

    print()


def show_summary():
    """Show a helpful summary."""
    print("=" * 70)
    print("💡 Quick Reference")
    print("=" * 70)
    print("""
  Use models with any GAMMA command:

    # Game mode
    gamma.py game --model ENGINE:MODEL

    # Comparison
    gamma.py comparison --models pytorch:MODEL1 ollama:MODEL2

    # Mind meld
    gamma.py mind-meld --models pytorch:MODEL1 pytorch:MODEL2

    # Benchmark
    gamma.py benchmark --models ENGINE:MODEL1 ENGINE:MODEL2

  Supported engines:
    ollama       - Ollama models (ollama:gemma2:2b)
    pytorch      - HuggingFace models (pytorch:google/gemma-2-2b-it)
    vllm         - Fast inference (vllm:google/gemma-2-2b-it)
    llamacpp     - GGUF files (llamacpp:./models/model.gguf)
    mlx_gpu      - Apple Silicon (mlx_gpu:mlx-community/model)
""")


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "GAMMA Available Models" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # List from all sources
    list_ollama_models()
    list_huggingface_models()
    list_local_gguf_files()
    show_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
