"""Model path resolution utilities for finding models in multiple locations."""

import os
from typing import Optional, List
from pathlib import Path


# Default model search paths (in order of priority)
DEFAULT_MODEL_SEARCH_PATHS = [
    # 1. Project-local models directory (symlinks to other locations)
    "{project_root}/models",

    # 2. Ollama models directory
    "/usr/share/ollama/.ollama/models",

    # 3. User's home Ollama directory
    "~/.ollama/models",

    # 4. HuggingFace cache (for transformer models)
    "~/.cache/huggingface/hub",
]


def get_project_root() -> Path:
    """Get the project root directory (where gamma/ is located)."""
    # This file is in src/core/, so go up two levels
    return Path(__file__).parent.parent.parent


def resolve_model_path(model_identifier: str, additional_paths: Optional[List[str]] = None) -> str:
    """
    Resolve a model identifier to an actual path.

    For HuggingFace models (e.g., "google/gemma-3-1b-it"), returns the identifier as-is.
    For local files/GGUF models, searches in multiple locations.

    Args:
        model_identifier: Model name or path (e.g., "google/gemma-3-1b-it" or "model.gguf")
        additional_paths: Optional list of additional paths to search

    Returns:
        Resolved path or original identifier
    """
    # If it's a HuggingFace-style identifier (org/model), return as-is
    if "/" in model_identifier and not model_identifier.startswith(("/", "~", ".")):
        # Check if it looks like a HuggingFace identifier (not a local path)
        parts = model_identifier.split("/")
        if len(parts) == 2 and not any(c in parts[0] for c in [".", " "]):
            return model_identifier

    # If it's already an absolute path that exists, return it
    if os.path.isabs(model_identifier) and os.path.exists(model_identifier):
        return model_identifier

    # If it's a relative path that exists, return absolute version
    if os.path.exists(model_identifier):
        return os.path.abspath(model_identifier)

    # Build search paths
    project_root = get_project_root()
    search_paths = []

    # Add any user-provided paths first
    if additional_paths:
        search_paths.extend(additional_paths)

    # Add default paths
    for path_template in DEFAULT_MODEL_SEARCH_PATHS:
        path = path_template.replace("{project_root}", str(project_root))
        path = os.path.expanduser(path)
        search_paths.append(path)

    # Search for the model file
    for search_dir in search_paths:
        if not os.path.isdir(search_dir):
            continue

        # Direct match in directory
        candidate = os.path.join(search_dir, model_identifier)
        if os.path.exists(candidate):
            return os.path.abspath(candidate)

        # For Ollama models, search in blobs directory
        if "ollama" in search_dir.lower():
            blobs_dir = os.path.join(search_dir, "blobs")
            if os.path.isdir(blobs_dir):
                candidate = os.path.join(blobs_dir, model_identifier)
                if os.path.exists(candidate):
                    return os.path.abspath(candidate)

                # Also check for sha256 prefixed files
                for filename in os.listdir(blobs_dir):
                    if filename.endswith(model_identifier) or model_identifier in filename:
                        candidate = os.path.join(blobs_dir, filename)
                        if os.path.exists(candidate):
                            return os.path.abspath(candidate)

    # If not found, return original identifier (might be downloaded by HuggingFace/framework)
    return model_identifier


def list_available_models(search_extensions: Optional[List[str]] = None) -> dict:
    """
    List all available models in the search paths.

    Args:
        search_extensions: File extensions to search for (default: ['.gguf', '.bin', '.safetensors'])

    Returns:
        Dictionary mapping location to list of model files
    """
    if search_extensions is None:
        search_extensions = ['.gguf', '.bin', '.safetensors', '.onnx']

    project_root = get_project_root()
    available_models = {}

    for path_template in DEFAULT_MODEL_SEARCH_PATHS:
        path = path_template.replace("{project_root}", str(project_root))
        path = os.path.expanduser(path)

        if not os.path.isdir(path):
            continue

        models = []

        # Walk the directory tree
        for root, dirs, files in os.walk(path):
            for filename in files:
                if any(filename.endswith(ext) for ext in search_extensions):
                    full_path = os.path.join(root, filename)
                    # Store relative path from search directory
                    rel_path = os.path.relpath(full_path, path)
                    models.append({
                        'filename': filename,
                        'relative_path': rel_path,
                        'full_path': full_path,
                        'size_mb': os.path.getsize(full_path) / (1024 * 1024)
                    })

        if models:
            available_models[path] = models

    return available_models


def setup_models_directory() -> Path:
    """
    Create the project-local models/ directory if it doesn't exist.

    Returns:
        Path to the models directory
    """
    project_root = get_project_root()
    models_dir = project_root / "models"

    models_dir.mkdir(exist_ok=True)

    return models_dir


def create_model_symlink(target_path: str, link_name: str) -> Optional[Path]:
    """
    Create a symlink in the models/ directory pointing to an external model.

    Args:
        target_path: Path to the actual model file
        link_name: Name for the symlink in models/ directory

    Returns:
        Path to created symlink, or None if failed
    """
    models_dir = setup_models_directory()

    target = Path(target_path).expanduser().resolve()
    if not target.exists():
        print(f"Warning: Target path does not exist: {target}")
        return None

    link_path = models_dir / link_name

    # Remove existing symlink if present
    if link_path.is_symlink():
        link_path.unlink()
    elif link_path.exists():
        print(f"Warning: {link_path} exists and is not a symlink. Not overwriting.")
        return None

    try:
        link_path.symlink_to(target)
        print(f"Created symlink: {link_path} -> {target}")
        return link_path
    except Exception as e:
        print(f"Failed to create symlink: {e}")
        return None
