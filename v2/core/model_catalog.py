"""
Model Catalog for GAMMA - Predefined models with metadata
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


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


# Predefined model catalogs for each engine
MODEL_CATALOG = {
    "pytorch": [
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
        
    def display_page(self) -> None:
        """Display current page of models."""
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_models))
        
        if not self.filtered_models:
            print("No models found for this engine.")
            return
            
        print(f"\n📦 Available Models (Page {self.current_page + 1}/{self.total_pages()}):")
        print("-" * 70)
        
        for i in range(start_idx, end_idx):
            model = self.filtered_models[i]
            num = i + 1
            
            # Format the display
            rec = "⭐" if model.recommended else "  "
            auth = "🔐" if model.requires_auth else "  "
            
            print(f"{rec} {num:2}. {model.name:<35} [{model.size:>4}] {model.memory_estimate:>6}")
            print(f"       {model.description}")
            if model.requires_auth:
                print(f"       {auth} Requires Hugging Face authentication")
            print()
        
        print("-" * 70)
        
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return max(1, (len(self.filtered_models) + self.page_size - 1) // self.page_size)
    
    def show_navigation_help(self) -> None:
        """Show navigation options."""
        print("\nOptions:")
        print("  • Enter model number (1-{})".format(len(self.filtered_models)))
        print("  • 'n' - Next page")
        print("  • 'p' - Previous page")
        print("  • 's' - Search/filter models")
        print("  • 'c' - Enter custom model path")
        print("  • 'r' - Show only recommended models")
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
                        print(f"\n✓ Selected: {selected.name}")
                        return selected.name
                    else:
                        print(f"Please enter a number between 1 and {len(self.filtered_models)}")
                except ValueError:
                    print("Invalid choice. Please try again.")


def get_model_info(engine: str, model_name: str) -> Optional[ModelInfo]:
    """Get information about a specific model."""
    models = MODEL_CATALOG.get(engine, [])
    for model in models:
        if model.name == model_name:
            return model
    return None