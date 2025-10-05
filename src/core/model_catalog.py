"""
Model Catalog for GAMMA - Predefined models with metadata
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os
from src.core.model_paths import list_available_models, get_project_root, resolve_model_path
from src.core.memory_estimator import check_model_fits, format_memory_estimate
from src.core.gpu_discovery import get_total_available_vram_mb


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    engine: str
    size: str  # e.g., "2B", "7B", "9B"
    description: str
    memory_estimate: str  # Rough memory requirement
    recommended: bool = False
    requires_auth: bool = True  # Most Gemma models need HF auth
    available_locally: bool = False  # Whether model exists on disk
    location: Optional[str] = None  # Path to local model if available


# Predefined model catalogs for each engine
MODEL_CATALOG = {
    "pytorch": [
        ModelInfo(
            "google/gemma-3-1b-it",
            "pytorch",
            "1B",
            "1B, Instruct, versatile.",
            "4-6GB",
            recommended=True
        ),
        ModelInfo(
            "google/gemma-3-4b-it",
            "pytorch",
            "4B",
            "4B, Instruct, good balance.",
            "12-16GB"
        ),
        ModelInfo(
            "google/gemma-3-12b-it",
            "pytorch",
            "12B",
            "12B, Instruct, powerful.",
            "32-48GB"
        ),
        ModelInfo(
            "google/gemma-3-27b-it",
            "pytorch",
            "27B",
            "27B, Instruct, very strong.",
            "64-96GB"
        ),
        ModelInfo(
            "google/gemma-3-1b",
            "pytorch",
            "1B",
            "1B, Base, for fine-tuning.",
            "4-6GB"
        ),
        ModelInfo(
            "google/gemma-3-4b",
            "pytorch",
            "4B",
            "4B, Base.",
            "12-16GB"
        ),
        ModelInfo(
            "google/gemma-3-12b",
            "pytorch",
            "12B",
            "12B, Base.",
            "32-48GB"
        ),
        ModelInfo(
            "google/gemma-3-27b",
            "pytorch",
            "27B",
            "27B, Base, very large.",
            "64-96GB"
        ),
        ModelInfo(
            "google/gemma-3n-e4b-it",
            "pytorch",
            "4B",
            "New 4B, Instruct, efficient.",
            "12-16GB"
        ),
        ModelInfo(
            "google/gemma-2b-it",
            "pytorch",
            "2B",
            "Gemma 2B Instruct - Lightweight, fast",
            "~8GB",
            recommended=True
        ),
        ModelInfo(
            "google/gemma-2b",
            "pytorch",
            "2B",
            "Gemma 2B Base - Pre-trained, no instruction tuning",
            "~8GB"
        ),
        ModelInfo(
            "google/gemma-2-2b-it",
            "pytorch",
            "2B",
            "Gemma 2 2B Instruct - Updated architecture",
            "~8GB",
            recommended=True
        ),
        ModelInfo(
            "google/gemma-7b-it",
            "pytorch",
            "7B",
            "Gemma 7B Instruct - Larger, more capable",
            "~28GB"
        ),
        ModelInfo(
            "google/gemma-7b",
            "pytorch",
            "7B",
            "Gemma 7B Base - Pre-trained, no instruction tuning",
            "~28GB"
        ),
        ModelInfo(
            "google/gemma-2-9b-it",
            "pytorch",
            "9B",
            "Gemma 2 9B Instruct - Large, high quality",
            "~36GB"
        ),
        ModelInfo(
            "google/gemma-2-9b",
            "pytorch",
            "9B",
            "Gemma 2 9B Base - Pre-trained, no instruction tuning",
            "~36GB"
        ),
        ModelInfo(
            "google/gemma-2-27b-it",
            "pytorch",
            "27B",
            "Gemma 2 27B Instruct - Very large, state-of-the-art",
            "~108GB"
        ),
        ModelInfo(
            "google/codegemma-2b",
            "pytorch",
            "2B",
            "CodeGemma 2B - Specialized for code",
            "~8GB"
        ),
        ModelInfo(
            "google/codegemma-7b-it",
            "pytorch",
            "7B",
            "CodeGemma 7B Instruct - Code generation",
            "~28GB"
        ),
        ModelInfo(
            "google/recurrentgemma-2b-it",
            "pytorch",
            "2B",
            "RecurrentGemma 2B - Griffin architecture",
            "~8GB"
        ),
    ],
    "tensorflow": [
        ModelInfo(
            "google/gemma-2b-it",
            "tensorflow",
            "2B",
            "Gemma 2B Instruct - TensorFlow version",
            "~8GB",
            recommended=True
        ),
        ModelInfo(
            "google/gemma-2b",
            "tensorflow",
            "2B",
            "Gemma 2B Base - TensorFlow version",
            "~8GB"
        ),
        ModelInfo(
            "google/gemma-7b-it",
            "tensorflow",
            "7B",
            "Gemma 7B Instruct - TensorFlow version",
            "~28GB"
        ),
        ModelInfo(
            "google/gemma-7b",
            "tensorflow",
            "7B",
            "Gemma 7B Base - TensorFlow version",
            "~28GB"
        ),
    ],
    "jax": [
        ModelInfo(
            "google/gemma-2b-it",
            "jax",
            "2B",
            "Gemma 2B Instruct - JAX/Flax version",
            "~8GB",
            recommended=True
        ),
        ModelInfo(
            "google/gemma-2b",
            "jax",
            "2B",
            "Gemma 2B Base - JAX/Flax version",
            "~8GB"
        ),
        ModelInfo(
            "google/gemma-7b-it",
            "jax",
            "7B",
            "Gemma 7B Instruct - JAX/Flax version",
            "~28GB"
        ),
        ModelInfo(
            "google/gemma-7b",
            "jax",
            "7B",
            "Gemma 7B Base - JAX/Flax version",
            "~28GB"
        ),
    ],
    "llamacpp": [
        ModelInfo(
            "gemma-2b-it-q4_k_m.gguf",
            "llamacpp",
            "2B",
            "Gemma 2B Instruct - 4-bit quantized GGUF",
            "~2GB",
            recommended=True,
            requires_auth=False
        ),
        ModelInfo(
            "gemma-2b-it-q5_k_m.gguf",
            "llamacpp",
            "2B",
            "Gemma 2B Instruct - 5-bit quantized GGUF",
            "~2.5GB",
            requires_auth=False
        ),
        ModelInfo(
            "gemma-2b-it-q8_0.gguf",
            "llamacpp",
            "2B",
            "Gemma 2B Instruct - 8-bit quantized GGUF",
            "~4GB",
            requires_auth=False
        ),
        ModelInfo(
            "gemma-7b-it-q4_k_m.gguf",
            "llamacpp",
            "7B",
            "Gemma 7B Instruct - 4-bit quantized GGUF",
            "~6GB",
            requires_auth=False
        ),
        ModelInfo(
            "gemma-7b-it-q5_k_m.gguf",
            "llamacpp",
            "7B",
            "Gemma 7B Instruct - 5-bit quantized GGUF",
            "~7.5GB",
            requires_auth=False
        ),
    ],
    "onnx": [
        ModelInfo(
            "gemma-2b-it-onnx",
            "onnx",
            "2B",
            "Gemma 2B Instruct - ONNX format",
            "~8GB",
            recommended=True,
            requires_auth=False
        ),
        ModelInfo(
            "gemma-7b-it-onnx",
            "onnx",
            "7B",
            "Gemma 7B Instruct - ONNX format",
            "~28GB",
            requires_auth=False
        ),
    ],
    "mlx": [
        ModelInfo(
            "mlx-community/gemma-2b-it",
            "mlx",
            "2B",
            "Gemma 2B Instruct - MLX optimized for Apple Silicon",
            "~8GB",
            recommended=True,
            requires_auth=False
        ),
        ModelInfo(
            "mlx-community/gemma-7b-it",
            "mlx",
            "7B",
            "Gemma 7B Instruct - MLX optimized for Apple Silicon",
            "~28GB",
            requires_auth=False
        ),
        ModelInfo(
            "mlx-community/gemma-2-2b-it",
            "mlx",
            "2B",
            "Gemma 2 2B Instruct - MLX optimized",
            "~8GB",
            requires_auth=False
        ),
        ModelInfo(
            "mlx-community/gemma-2-9b-it",
            "mlx",
            "9B",
            "Gemma 2 9B Instruct - MLX optimized",
            "~36GB",
            requires_auth=False
        ),
    ]
}


class ModelSelector:
    """Interactive model selection with paging and search."""

    def __init__(self, engine: str):
        self.engine = engine
        self.models = MODEL_CATALOG.get(engine, [])
        self.page_size = 5
        self.current_page = 0
        self.filtered_models = self.models.copy()
        self.local_models = []
        self._discover_local_models()

    def _discover_local_models(self) -> None:
        """Discover locally available models (GGUF, ONNX, etc.)."""
        try:
            available = list_available_models()

            for location, models in available.items():
                for model in models:
                    # Only show models relevant to this engine
                    filename = model['filename']

                    if self.engine == 'llamacpp' and filename.endswith('.gguf'):
                        # Check if this model is already in catalog
                        existing = any(m.name == filename for m in self.models)
                        if not existing:
                            # Add new local GGUF model
                            size_mb = model['size_mb']
                            size_str = f"{size_mb / 1024:.1f}GB" if size_mb > 1024 else f"{size_mb:.0f}MB"

                            self.local_models.append(ModelInfo(
                                name=filename,
                                engine=self.engine,
                                size="?",
                                description=f"Local GGUF - {location}",
                                memory_estimate=size_str,
                                recommended=False,
                                requires_auth=False,
                                available_locally=True,
                                location=model['full_path']
                            ))
                        else:
                            # Mark existing catalog model as available
                            for m in self.models:
                                if m.name == filename:
                                    m.available_locally = True
                                    m.location = model['full_path']

                    elif self.engine == 'onnx' and filename.endswith('.onnx'):
                        existing = any(m.name == filename for m in self.models)
                        if not existing:
                            size_mb = model['size_mb']
                            size_str = f"{size_mb / 1024:.1f}GB" if size_mb > 1024 else f"{size_mb:.0f}MB"

                            self.local_models.append(ModelInfo(
                                name=filename,
                                engine=self.engine,
                                size="?",
                                description=f"Local ONNX - {location}",
                                memory_estimate=size_str,
                                recommended=False,
                                requires_auth=False,
                                available_locally=True,
                                location=model['full_path']
                            ))

            # Add local models to the beginning of the list
            if self.local_models:
                self.models = self.local_models + self.models
                self.filtered_models = self.models.copy()

        except Exception as e:
            # If discovery fails, just continue with catalog models
            pass

    def display_page(self) -> None:
        """Display current page of models."""
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_models))
        
        if not self.filtered_models:
            print("No models found for this engine.")
            return

        print(f"\n📦 Available Models (Page {self.current_page + 1}/{self.total_pages()}):")
        print("-" * 80)

        for i in range(start_idx, end_idx):
            model = self.filtered_models[i]
            num = i + 1

            # Format the display
            rec = "⭐" if model.recommended else "  "
            local = "💾" if model.available_locally else "☁️ "
            auth = "🔐" if model.requires_auth and not model.available_locally else "  "

            print(f"{local} {rec} {num:2}. {model.name:<40} [{model.size:>4}] {model.memory_estimate:>6}")
            print(f"          {model.description}")

            if model.available_locally:
                # Show abbreviated path
                if model.location:
                    short_location = model.location
                    if "ollama" in short_location.lower():
                        short_location = "...ollama/models/blobs/..."
                    elif str(get_project_root()) in short_location:
                        short_location = short_location.replace(str(get_project_root()), ".")
                    print(f"          ✓ Local: {short_location}")
            elif model.requires_auth:
                print(f"          {auth} Download: HuggingFace (requires auth)")
            else:
                print(f"          ☁️  Download: HuggingFace (auto-download)")

            print()

        print("-" * 80)
        
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return max(1, (len(self.filtered_models) + self.page_size - 1) // self.page_size)
    
    def show_navigation_help(self) -> None:
        """Show navigation options."""
        local_count = sum(1 for m in self.filtered_models if m.available_locally)
        cloud_count = len(self.filtered_models) - local_count

        print("\nLegend: 💾=Local  ☁️=Download  ⭐=Recommended  🔐=Auth Required")
        print(f"Status: {local_count} local, {cloud_count} downloadable")
        print("\nOptions:")
        print("  • Enter model number (1-{})".format(len(self.filtered_models)))
        print("  • 'n' - Next page")
        print("  • 'p' - Previous page")
        print("  • 's' - Search/filter models")
        print("  • 'c' - Enter custom model path")
        print("  • 'r' - Show only recommended models")
        print("  • 'l' - Show only local models")
        print("  • 'a' - Show all models")
        print("  • 'q' - Cancel selection")
    
    def filter_models(self, search_term: str) -> None:
        """Filter models based on search term."""
        search_lower = search_term.lower()
        self.filtered_models = [
            m for m in self.models
            if search_lower in m.name.lower() or
               search_lower in m.description.lower() or
               search_lower in m.size.lower()
        ]
        self.current_page = 0
    
    def show_recommended_only(self) -> None:
        """Show only recommended models."""
        self.filtered_models = [m for m in self.models if m.recommended]
        self.current_page = 0

    def show_local_only(self) -> None:
        """Show only locally available models."""
        self.filtered_models = [m for m in self.models if m.available_locally]
        self.current_page = 0

    def reset_filter(self) -> None:
        """Reset to show all models."""
        self.filtered_models = self.models.copy()
        self.current_page = 0
    
    def select_model(self) -> Optional[str]:
        """Interactive model selection with paging."""
        if not self.models:
            print(f"\nNo predefined models for {self.engine} engine.")
            custom = input("Enter custom model path (or 'q' to cancel): ").strip()
            return None if custom.lower() == 'q' else custom
        
        while True:
            self.display_page()
            self.show_navigation_help()
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'q':
                return None
            elif choice == 'n':
                if self.current_page < self.total_pages() - 1:
                    self.current_page += 1
                else:
                    print("Already on last page.")
            elif choice == 'p':
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    print("Already on first page.")
            elif choice == 's':
                search = input("Enter search term: ").strip()
                self.filter_models(search)
                print(f"Found {len(self.filtered_models)} matching models.")
            elif choice == 'r':
                self.show_recommended_only()
                print(f"Showing {len(self.filtered_models)} recommended models.")
            elif choice == 'l':
                self.show_local_only()
                if len(self.filtered_models) == 0:
                    print("No local models found. Models will be auto-downloaded on first use.")
                else:
                    print(f"Showing {len(self.filtered_models)} local models.")
            elif choice == 'a':
                self.reset_filter()
                print(f"Showing all {len(self.filtered_models)} models.")
            elif choice == 'c':
                custom = input("Enter custom model path: ").strip()
                if custom:
                    return custom
            else:
                try:
                    model_num = int(choice)
                    if 1 <= model_num <= len(self.filtered_models):
                        selected = self.filtered_models[model_num - 1]

                        # Check memory requirements
                        self._check_memory_before_selection(selected)

                        print(f"\n✓ Selected: {selected.name}")
                        return selected.name
                    else:
                        print(f"Please enter a number between 1 and {len(self.filtered_models)}")
                except ValueError:
                    print("Invalid choice. Please try again.")

    def _check_memory_before_selection(self, model: ModelInfo) -> None:
        """Check if model fits in available VRAM and warn user."""
        try:
            # Resolve model path
            model_path = resolve_model_path(model.name)

            # Get available VRAM
            available_vram_mb = get_total_available_vram_mb()

            # If no GPU, skip check
            if available_vram_mb == 0:
                print("\n⚠️  No GPU detected - model will run on CPU (slow)")
                return

            # Check if model fits
            fits, message, estimate = check_model_fits(model_path, available_vram_mb)

            print(f"\n📊 Memory Estimate:")
            print(format_memory_estimate(estimate))
            print(f"\n{message}")

            if not fits:
                confirm = input("\nContinue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Selection cancelled.")
                    return

        except Exception as e:
            # If estimation fails, just warn and continue
            print(f"\n⚠️  Could not estimate memory requirements: {e}")
            pass


def get_model_info(engine: str, model_name: str) -> Optional[ModelInfo]:
    """Get information about a specific model."""
    models = MODEL_CATALOG.get(engine, [])
    for model in models:
        if model.name == model_name:
            return model
    return None