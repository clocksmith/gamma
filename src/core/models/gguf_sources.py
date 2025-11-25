"""
Unified GGUF Source Management

Provides a streamlined interface for discovering GGUF models from multiple sources:
- Ollama (via ollama CLI)
- Local filesystem (direct GGUF files)
- HuggingFace Hub (GGUF models)

This consolidates the scattered logic across model_catalog.py, model_discovery.py,
and model_paths.py into a single, maintainable interface.
"""

import os
import struct
import subprocess
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from src.core.hardware.gguf_parser import GGUFMetadata
from src.core.models.model_paths import get_project_root, DEFAULT_MODEL_SEARCH_PATHS


@dataclass
class GGUFModel:
    """Unified representation of a GGUF model from any source."""
    name: str  # Display name (e.g., "gemma3:4b" or "model.gguf")
    path: str  # Full path to GGUF file
    source: str  # "ollama", "local", "huggingface"
    size_bytes: int  # File size
    metadata: Optional[Dict] = None  # Parsed GGUF metadata

    @property
    def size_gb(self) -> float:
        """Get size in GB."""
        return self.size_bytes / (1024 ** 3)

    @property
    def size_display(self) -> str:
        """Get human-readable size."""
        if self.size_gb >= 1:
            return f"{self.size_gb:.1f}GB"
        else:
            return f"{self.size_bytes / (1024 ** 2):.0f}MB"

    @property
    def quantization(self) -> str:
        """Get quantization level from metadata."""
        if self.metadata:
            return self.metadata.get('quantization', 'unknown')
        return 'unknown'

    @property
    def param_size(self) -> Optional[int]:
        """Get parameter count in billions."""
        if self.metadata:
            return self.metadata.get('param_billions')
        return None

    @property
    def unique_key(self) -> str:
        """Get unique key for deduplication (based on resolved path)."""
        return os.path.realpath(self.path)


class GGUFSourceManager:
    """Manages discovery and access to GGUF models from multiple sources."""

    def __init__(self):
        self.models: List[GGUFModel] = []
        self._discovered_paths: Set[str] = set()  # For deduplication

    def discover_all(self) -> List[GGUFModel]:
        """
        Discover GGUF models from all sources.

        Returns:
            List of GGUFModel objects, deduplicated by actual file path
        """
        self.models = []
        self._discovered_paths = set()

        # Discover from each source
        self._discover_ollama()
        self._discover_local()
        self._discover_huggingface()

        return self.models

    def _discover_ollama(self) -> None:
        """Discover GGUF models from Ollama."""
        try:
            # List all Ollama models
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 1:
                    continue

                model_name = parts[0]
                size_str = parts[2] if len(parts) > 2 else "?"

                # Get the actual GGUF blob path
                try:
                    show_result = subprocess.run(
                        ['ollama', 'show', model_name, '--modelfile'],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=5
                    )

                    # Parse the FROM line to get the blob path
                    for show_line in show_result.stdout.split('\n'):
                        if show_line.startswith('FROM '):
                            blob_path = show_line.split('FROM ')[1].strip()

                            # Check if we've already discovered this file
                            real_path = os.path.realpath(blob_path)
                            if real_path in self._discovered_paths:
                                continue

                            # Verify file exists and is GGUF
                            if not os.path.exists(blob_path):
                                continue

                            # Parse metadata
                            metadata = None
                            try:
                                gguf_meta = GGUFMetadata(blob_path)
                                if gguf_meta.valid:
                                    metadata = gguf_meta.metadata
                            except (IOError, ValueError, struct.error):
                                pass  # Invalid or unreadable GGUF file

                            # Get file size
                            size_bytes = os.path.getsize(blob_path)

                            # Create model entry
                            model = GGUFModel(
                                name=model_name,
                                path=blob_path,
                                source='ollama',
                                size_bytes=size_bytes,
                                metadata=metadata
                            )

                            self.models.append(model)
                            self._discovered_paths.add(real_path)
                            break

                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    # Can't get blob path for this model, skip it
                    continue

        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Ollama not installed or not responding
            pass

    def _discover_local(self) -> None:
        """Discover GGUF models from local filesystem."""
        # Build search paths
        project_root = get_project_root()
        search_paths = []

        for path_template in DEFAULT_MODEL_SEARCH_PATHS:
            path = path_template.replace("{project_root}", str(project_root))
            path = os.path.expanduser(path)

            if os.path.isdir(path):
                search_paths.append(path)

        # Also add current directory
        if os.getcwd() not in search_paths:
            search_paths.append(os.getcwd())

        # Search for GGUF files
        for search_dir in search_paths:
            try:
                search_path = Path(search_dir)

                # Recursively find all .gguf files
                for gguf_file in search_path.rglob('*.gguf'):
                    if not gguf_file.is_file():
                        continue

                    file_path = str(gguf_file)
                    real_path = os.path.realpath(file_path)

                    # Skip if already discovered
                    if real_path in self._discovered_paths:
                        continue

                    # Parse metadata
                    metadata = None
                    try:
                        gguf_meta = GGUFMetadata(file_path)
                        if gguf_meta.valid:
                            metadata = gguf_meta.metadata
                    except (IOError, ValueError, struct.error):
                        pass  # Invalid or unreadable GGUF file

                    # Get file size
                    size_bytes = gguf_file.stat().st_size

                    # Create model entry
                    model = GGUFModel(
                        name=gguf_file.name,
                        path=file_path,
                        source='local',
                        size_bytes=size_bytes,
                        metadata=metadata
                    )

                    self.models.append(model)
                    self._discovered_paths.add(real_path)

            except (PermissionError, OSError):
                # Skip directories that can't be accessed
                continue

    def _discover_huggingface(self) -> None:
        """Discover GGUF models from HuggingFace cache."""
        # Find HF cache directory
        hf_cache_dirs = [
            os.path.expanduser("~/.cache/huggingface/hub"),
            os.path.expanduser("~/Library/Caches/huggingface/hub"),  # macOS
        ]

        hf_cache = None
        for cache_dir in hf_cache_dirs:
            if os.path.exists(cache_dir):
                hf_cache = cache_dir
                break

        if hf_cache is None:
            return

        # Search for GGUF files in HF cache
        try:
            cache_path = Path(hf_cache)

            # HF cache structure: models--org--model/snapshots/hash/*.gguf
            for model_dir in cache_path.glob('models--*'):
                if not model_dir.is_dir():
                    continue

                snapshots_dir = model_dir / 'snapshots'
                if not snapshots_dir.exists():
                    continue

                # Extract model name from directory
                model_name = model_dir.name.replace('models--', '').replace('--', '/')

                # Search all snapshots for GGUF files
                for gguf_file in snapshots_dir.rglob('*.gguf'):
                    if not gguf_file.is_file():
                        continue

                    file_path = str(gguf_file)
                    real_path = os.path.realpath(file_path)

                    # Skip if already discovered
                    if real_path in self._discovered_paths:
                        continue

                    # Parse metadata
                    metadata = None
                    try:
                        gguf_meta = GGUFMetadata(file_path)
                        if gguf_meta.valid:
                            metadata = gguf_meta.metadata
                    except (IOError, ValueError, struct.error):
                        pass  # Invalid or unreadable GGUF file

                    # Get file size
                    size_bytes = gguf_file.stat().st_size

                    # Create model entry with HF-style name
                    display_name = f"{model_name}/{gguf_file.name}"

                    model = GGUFModel(
                        name=display_name,
                        path=file_path,
                        source='huggingface',
                        size_bytes=size_bytes,
                        metadata=metadata
                    )

                    self.models.append(model)
                    self._discovered_paths.add(real_path)

        except (PermissionError, OSError):
            # Failed to scan HF cache
            pass

    def get_by_source(self, source: str) -> List[GGUFModel]:
        """Get models from a specific source."""
        return [m for m in self.models if m.source == source]

    def get_by_name(self, name: str) -> Optional[GGUFModel]:
        """Get model by name (case-insensitive)."""
        name_lower = name.lower()
        for model in self.models:
            if model.name.lower() == name_lower:
                return model
        return None

    def get_by_path(self, path: str) -> Optional[GGUFModel]:
        """Get model by path."""
        real_path = os.path.realpath(path)
        for model in self.models:
            if model.unique_key == real_path:
                return model
        return None

    def filter_by_size(self, max_gb: Optional[float] = None,
                      min_gb: Optional[float] = None) -> List[GGUFModel]:
        """Filter models by size."""
        filtered = self.models

        if max_gb is not None:
            filtered = [m for m in filtered if m.size_gb <= max_gb]

        if min_gb is not None:
            filtered = [m for m in filtered if m.size_gb >= min_gb]

        return filtered

    def filter_by_quantization(self, quant_type: str) -> List[GGUFModel]:
        """Filter models by quantization type (e.g., 'Q4_K_M')."""
        quant_lower = quant_type.lower()
        return [m for m in self.models
                if m.quantization.lower() == quant_lower]

    def get_smallest(self) -> Optional[GGUFModel]:
        """Get the smallest available model."""
        if not self.models:
            return None
        return min(self.models, key=lambda m: m.size_bytes)

    def sort_by_size(self, ascending: bool = True) -> List[GGUFModel]:
        """Get models sorted by size."""
        return sorted(self.models, key=lambda m: m.size_bytes,
                     reverse=not ascending)

    def sort_by_source(self) -> List[GGUFModel]:
        """Get models sorted by source (ollama, local, huggingface)."""
        source_order = {'ollama': 0, 'local': 1, 'huggingface': 2}
        return sorted(self.models,
                     key=lambda m: (source_order.get(m.source, 3), m.name))

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            'total': len(self.models),
            'ollama': len(self.get_by_source('ollama')),
            'local': len(self.get_by_source('local')),
            'huggingface': len(self.get_by_source('huggingface')),
            'total_size_gb': sum(m.size_gb for m in self.models)
        }


def quick_discover_gguf() -> GGUFSourceManager:
    """
    Quick helper to discover all GGUF models.

    Returns:
        GGUFSourceManager with all discovered models
    """
    manager = GGUFSourceManager()
    manager.discover_all()
    return manager
