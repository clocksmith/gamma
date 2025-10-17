"""
Interactive Menu System for GAMMA - Provides full CLI configuration
"""

from typing import Optional, Dict, Any, List, Tuple
from src.core import config as cfg
from src.ui import components as uic
from src.core.menu import interactive_prompts as prompts
from src.core.models.model_catalog import ModelSelector, get_model_info
from src.core.hardware.gpu_discovery import get_gpu_info, format_gpu_info


class InteractiveMenu:
    """Interactive menu system for configuring and launching GAMMA."""
    
    def __init__(self):
        self.config = {}
        
    def show_main_menu(self) -> Optional[Dict[str, Any]]:
        """Show the main menu and return configuration."""
        uic.print_separator()
        print(uic.color_text("🎮 GAMMA - Interactive Configuration", cfg.COLOR_CYAN))

        # Show GPU info
        print(format_gpu_info(get_gpu_info()))

        print("\n⚡ Quick Start Options:")
        print("  1. Just Play! (Classic with defaults)")
        print("  2. Quick Tutorial (Start learning immediately)")
        print("  3. Quick Compare (2 small models)")
        print("\n🔧 Advanced Options:")
        print("  4. Classic Game - Configure & predict the model's next token")
        print("  5. Tutorial Mode - Configure & learn how LLMs work")
        print("  6. Comparison Mode - Configure & compare multiple models")
        print("  7. Mind Meld Mode - Configure & meld multiple models")
        print("  8. Exit")

        choice = prompts.get_user_input(
            "\nSelect mode (1-8)",
            valid_choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            allow_quit=True
        )
        
        if choice == cfg.SHORTCUT_QUIT or choice == "8":
            return None
            
        if choice == "1":
            # Quick play classic with defaults
            return self._quick_play_classic()
        elif choice == "2":
            # Quick tutorial with defaults
            return self._quick_play_tutorial()
        elif choice == "3":
            # Quick comparison with 2 small models
            return self._quick_play_comparison()
        elif choice == "4":
            return self._configure_classic_mode()
        elif choice == "5":
            return self._configure_tutorial_mode()
        elif choice == "6":
            return self._configure_comparison_mode()
        elif choice == "7":
            return self._configure_mind_meld_mode()
            
        return None
    
    def _configure_classic_mode(self) -> Dict[str, Any]:
        """Configure classic game mode."""
        config = {
            'mode': 'classic',
            'tutorial': False,
            'comparison': False
        }
        
        print(uic.color_text("\n⚙️  Classic Game Configuration", cfg.COLOR_YELLOW))
        
        # Model selection
        config.update(self._select_model_interactively())
        
        # Game parameters
        print("\n📊 Game Parameters:")
        
        # Steps
        steps_input = prompts.get_user_input(
            f"Number of rounds (default: {cfg.DEFAULT_MAX_DECODE_STEPS})",
            allow_empty=True
        )
        if steps_input and steps_input != cfg.SHORTCUT_QUIT:
            try:
                config['steps'] = int(steps_input)
            except ValueError:
                config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS
        else:
            config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS
        
        # Temperature
        temp_input = prompts.get_user_input(
            f"Temperature (0.1-2.0, default: {cfg.DEFAULT_TEMPERATURE})",
            allow_empty=True
        )
        if temp_input and temp_input != cfg.SHORTCUT_QUIT:
            try:
                config['temperature'] = float(temp_input)
            except ValueError:
                config['temperature'] = cfg.DEFAULT_TEMPERATURE
        else:
            config['temperature'] = cfg.DEFAULT_TEMPERATURE
        
        # Top-K
        topk_input = prompts.get_user_input(
            f"Top-K filtering (default: {cfg.DEFAULT_TOP_K})",
            allow_empty=True
        )
        if topk_input and topk_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_k'] = int(topk_input)
            except ValueError:
                config['top_k'] = cfg.DEFAULT_TOP_K
        else:
            config['top_k'] = cfg.DEFAULT_TOP_K
        
        # Top-P
        topp_input = prompts.get_user_input(
            f"Top-P filtering (0.0-1.0, default: {cfg.DEFAULT_TOP_P})",
            allow_empty=True
        )
        if topp_input and topp_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_p'] = float(topp_input)
            except ValueError:
                config['top_p'] = cfg.DEFAULT_TOP_P
        else:
            config['top_p'] = cfg.DEFAULT_TOP_P
        
        # Advanced options
        print("\n🔧 Advanced Options:")
        
        # Show attention
        show_attn = prompts.get_user_input(
            "Show attention heatmap? (y/n, default: y)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['show_attention'] = show_attn != "n"
        
        # Number of choices
        num_choices_input = prompts.get_user_input(
            f"Number of choices per round (default: {cfg.DEFAULT_NUM_CHOICES})",
            allow_empty=True
        )
        if num_choices_input and num_choices_input != cfg.SHORTCUT_QUIT:
            try:
                config['num_choices'] = int(num_choices_input)
            except ValueError:
                config['num_choices'] = cfg.DEFAULT_NUM_CHOICES
        else:
            config['num_choices'] = cfg.DEFAULT_NUM_CHOICES
        
        # Permutation length
        perm_len_input = prompts.get_user_input(
            f"Tokens per choice (default: {cfg.DEFAULT_PERMUTATION_LENGTH})",
            allow_empty=True
        )
        if perm_len_input and perm_len_input != cfg.SHORTCUT_QUIT:
            try:
                config['permutation_length'] = int(perm_len_input)
            except ValueError:
                config['permutation_length'] = cfg.DEFAULT_PERMUTATION_LENGTH
        else:
            config['permutation_length'] = cfg.DEFAULT_PERMUTATION_LENGTH
        
        # Focus words mode
        focus_words = prompts.get_user_input(
            "Focus on word-like tokens? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['focus_words'] = focus_words == "y"
        
        # Player choice mode
        player_mode = prompts.get_user_input(
            "Player choice mode (your guess drives generation)? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['player_choice_mode'] = player_mode == "y"
        
        # Verbose mode
        verbose = prompts.get_user_input(
            "Enable detailed explanations? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['verbose'] = verbose == "y"
        
        # Model-specific options
        if config.get('engine') == 'pytorch':
            print("\n🔥 PyTorch-specific Options:")
            
            # 4-bit quantization
            quant_4bit = prompts.get_user_input(
                "Use 4-bit quantization? (reduces memory, y/n, default: n)",
                valid_choices=["y", "n", ""],
                allow_empty=True
            )
            config['load_in_4bit'] = quant_4bit == "y"
            
            # 8-bit quantization
            if not config['load_in_4bit']:
                quant_8bit = prompts.get_user_input(
                    "Use 8-bit quantization? (y/n, default: n)",
                    valid_choices=["y", "n", ""],
                    allow_empty=True
                )
                config['load_in_8bit'] = quant_8bit == "y"
            
            # KV cache
            kv_cache = prompts.get_user_input(
                "Use KV cache? (faster generation, y/n, default: y)",
                valid_choices=["y", "n", ""],
                allow_empty=True
            )
            config['use_kv_cache'] = kv_cache != "n"
        
        return config
    
    def _configure_tutorial_mode(self) -> Dict[str, Any]:
        """Configure tutorial mode."""
        config = {
            'mode': 'tutorial',
            'tutorial': True,
            'comparison': False
        }
        
        print(uic.color_text("\n🎓 Tutorial Mode Configuration", cfg.COLOR_YELLOW))
        
        # Model selection for demonstrations
        print("\nSelect model for demonstrations:")
        config.update(self._select_model_interactively())
        
        # Verbose mode
        verbose = prompts.get_user_input(
            "\nEnable verbose explanations? (y/n, default: y)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['verbose'] = verbose != "n"
        
        # Show attention in demos
        show_attn = prompts.get_user_input(
            "Show attention visualizations? (y/n, default: y)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['show_attention'] = show_attn != "n"
        
        # Set default parameters for tutorial
        config['temperature'] = 0.7
        config['top_k'] = 8
        config['top_p'] = 0.95
        config['steps'] = 5  # Short demos in tutorial
        
        return config
    
    def _configure_comparison_mode(self) -> Dict[str, Any]:
        """Configure comparison mode."""
        config = {
            'mode': 'comparison',
            'tutorial': False,
            'comparison': True,
            'comparison_models': []
        }
        
        print(uic.color_text("\n🔬 Comparison Mode Configuration", cfg.COLOR_YELLOW))
        
        # Select models to compare
        print("\nSelect models to compare (minimum 2):")
        
        models = []
        model_count = 1
        
        while len(models) < 2 or model_count <= 5:  # Max 5 models
            print(f"\n📦 Model {model_count}:")
            
            if len(models) >= 2:
                done = prompts.get_user_input(
                    "Add another model? (y/n)",
                    valid_choices=["y", "n"],
                    allow_empty=False
                )
                if done == "n":
                    break
            
            model_config = self._select_model_interactively(for_comparison=True)
            if model_config.get('engine') and model_config.get('model'):
                model_spec = f"{model_config['engine']}:{model_config['model']}"
                models.append(model_spec)
                print(f"  ✓ Added: {model_spec}")
                model_count += 1
        
        config['comparison_models'] = models
        
        # Game parameters
        print("\n📊 Comparison Parameters:")
        
        # Steps
        steps_input = prompts.get_user_input(
            f"Number of rounds (default: {cfg.DEFAULT_MAX_DECODE_STEPS})",
            allow_empty=True
        )
        if steps_input and steps_input != cfg.SHORTCUT_QUIT:
            try:
                config['steps'] = int(steps_input)
            except ValueError:
                config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS
        else:
            config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS
        
        # Temperature
        temp_input = prompts.get_user_input(
            f"Temperature for all models (default: {cfg.DEFAULT_TEMPERATURE})",
            allow_empty=True
        )
        if temp_input and temp_input != cfg.SHORTCUT_QUIT:
            try:
                config['temperature'] = float(temp_input)
            except ValueError:
                config['temperature'] = cfg.DEFAULT_TEMPERATURE
        else:
            config['temperature'] = cfg.DEFAULT_TEMPERATURE
        
        # Top-K
        topk_input = prompts.get_user_input(
            f"Top-K filtering (default: {cfg.DEFAULT_TOP_K})",
            allow_empty=True
        )
        if topk_input and topk_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_k'] = int(topk_input)
            except ValueError:
                config['top_k'] = cfg.DEFAULT_TOP_K
        else:
            config['top_k'] = cfg.DEFAULT_TOP_K
        
        # Top-P
        topp_input = prompts.get_user_input(
            f"Top-P filtering (default: {cfg.DEFAULT_TOP_P})",
            allow_empty=True
        )
        if topp_input and topp_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_p'] = float(topp_input)
            except ValueError:
                config['top_p'] = cfg.DEFAULT_TOP_P
        else:
            config['top_p'] = cfg.DEFAULT_TOP_P
        
        # Show attention
        show_attn = prompts.get_user_input(
            "Show attention comparisons? (y/n, default: y)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['show_attention'] = show_attn != "n"
        
        # Player voting mode
        player_mode = prompts.get_user_input(
            "Enable player voting mode? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['player_choice_mode'] = player_mode == "y"
        
        # Verbose mode
        verbose = prompts.get_user_input(
            "Enable verbose output? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['verbose'] = verbose == "y"
        
        return config

    def _configure_mind_meld_mode(self) -> Dict[str, Any]:
        """Configure Mind Meld mode."""
        config = {
            'mode': 'mind_meld',
            'tutorial': False,
            'comparison': False,
            'mind_meld': True,
            'meld_models': []
        }

        print(uic.color_text("\n🧠 Mind Meld Mode Configuration", cfg.COLOR_YELLOW))

        models = []
        model_count = 1
        while len(models) < 2 or model_count <= 5:
            print(f"\n🤝 Model {model_count}:")

            if len(models) >= 2:
                add_more = prompts.get_user_input(
                    "Add another model to the meld? (y/n)",
                    valid_choices=["y", "n"],
                    allow_empty=False
                )
                if add_more == "n":
                    break

            model_config = self._select_model_interactively(for_comparison=True)
            engine = model_config.get('engine')
            model_name = model_config.get('model')

            if engine and model_name:
                model_spec = f"{engine}:{model_name}"
                models.append(model_spec)
                print(f"  ✓ Added: {model_spec}")
                model_count += 1
            else:
                print(uic.color_text("Model selection cancelled; returning to menu.", cfg.COLOR_YELLOW))
                break

        config['meld_models'] = models

        # Generation parameters
        print("\n📊 Generation Parameters:")

        steps_input = prompts.get_user_input(
            f"Number of rounds (default: {cfg.DEFAULT_MAX_DECODE_STEPS})",
            allow_empty=True
        )
        if steps_input and steps_input != cfg.SHORTCUT_QUIT:
            try:
                config['steps'] = int(steps_input)
            except ValueError:
                config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS
        else:
            config['steps'] = cfg.DEFAULT_MAX_DECODE_STEPS

        temp_input = prompts.get_user_input(
            f"Temperature (0.1-2.0, default: {cfg.DEFAULT_TEMPERATURE})",
            allow_empty=True
        )
        if temp_input and temp_input != cfg.SHORTCUT_QUIT:
            try:
                config['temperature'] = float(temp_input)
            except ValueError:
                config['temperature'] = cfg.DEFAULT_TEMPERATURE
        else:
            config['temperature'] = cfg.DEFAULT_TEMPERATURE

        topk_input = prompts.get_user_input(
            f"Top-K filtering (default: {cfg.DEFAULT_TOP_K})",
            allow_empty=True
        )
        if topk_input and topk_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_k'] = int(topk_input)
            except ValueError:
                config['top_k'] = cfg.DEFAULT_TOP_K
        else:
            config['top_k'] = cfg.DEFAULT_TOP_K

        topp_input = prompts.get_user_input(
            f"Top-P filtering (default: {cfg.DEFAULT_TOP_P})",
            allow_empty=True
        )
        if topp_input and topp_input != cfg.SHORTCUT_QUIT:
            try:
                config['top_p'] = float(topp_input)
            except ValueError:
                config['top_p'] = cfg.DEFAULT_TOP_P
        else:
            config['top_p'] = cfg.DEFAULT_TOP_P

        # Swap strategy selection
        print("\n🔄 Swap Strategy:")
        print("  1. Pattern-based (swap on punctuation)")
        print("  2. Fixed interval")
        print("  3. Round-robin")
        print("  4. Random")

        strategy_choice = prompts.get_user_input(
            "Select strategy (1-4, default: 1)",
            valid_choices=["1", "2", "3", "4", ""],
            allow_empty=True
        )

        strategy_map = {
            "1": "pattern",
            "2": "fixed",
            "3": "round_robin",
            "4": "random",
            "": "pattern"
        }
        config['swap_strategy'] = strategy_map.get(strategy_choice, "pattern")

        if config['swap_strategy'] in ("fixed", "fixed_interval"):
            interval_input = prompts.get_user_input(
                "Swap interval in tokens (default: 5)",
                allow_empty=True
            )
            if interval_input and interval_input != cfg.SHORTCUT_QUIT:
                try:
                    config['fixed_interval'] = int(interval_input)
                except ValueError:
                    config['fixed_interval'] = 5
            else:
                config['fixed_interval'] = 5

        # Ensemble options
        print("\n🤖 Ensemble & Blending:")
        use_weighted = prompts.get_user_input(
            "Use weighted averaging of model probabilities? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['use_weighted_average'] = use_weighted == "y"

        use_abe = prompts.get_user_input(
            "Enable Agreement-Based Ensembling (ABE)? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['use_abe'] = use_abe == "y"

        use_blending = prompts.get_user_input(
            "Blend logits from all models instead of swapping? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['use_blending'] = use_blending == "y"
        config['blend_strategy'] = 'weighted_average'
        config['alignment_strategy'] = 'semantic'
        config['use_enhanced'] = False

        stats_tracker = prompts.get_user_input(
            "Track detailed Mind Meld statistics? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['use_stats_tracker'] = stats_tracker == "y"
        if config['use_stats_tracker']:
            stats_path = prompts.get_user_input(
                "Optional path to save stats (press Enter to skip)",
                allow_empty=True
            )
            if stats_path and stats_path != cfg.SHORTCUT_QUIT:
                config['stats_file'] = stats_path

        # Prompt & display options
        default_prompt = "In a world where two minds are better than one,"
        prompt_val = prompts.get_user_input(
            "Initial prompt (leave empty for default)",
            allow_empty=True
        )
        if prompt_val and prompt_val != cfg.SHORTCUT_QUIT:
            config['initial_prompt'] = prompt_val
        else:
            config['initial_prompt'] = default_prompt

        show_attn = prompts.get_user_input(
            "Show attention visualization? (y/n, default: y)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['show_attention'] = show_attn != "n"

        verbose = prompts.get_user_input(
            "Enable verbose Mind Meld logging? (y/n, default: n)",
            valid_choices=["y", "n", ""],
            allow_empty=True
        )
        config['verbose'] = verbose == "y"

        return config

    def _select_model_interactively(self, for_comparison: bool = False) -> Dict[str, Any]:
        """Interactive model selection with enhanced catalog."""
        config = {}

        # Check if Ollama models are available
        ollama_available = self._check_ollama_availability()
        hf_authenticated = self._check_huggingface_auth()

        # Engine selection with smart defaults
        print("\n🚀 Select Engine:")
        print("  1. llama.cpp (GGUF models - local Ollama, HuggingFace, files)")
        if ollama_available:
            print("     ✓ Ollama models detected - will use llama.cpp")
        print("  2. PyTorch (HuggingFace Transformers)")
        if not hf_authenticated:
            print("     ⚠️  May require HuggingFace authentication for some models")
        print("  3. TensorFlow (experimental)")
        print("  4. JAX (experimental)")
        print("  5. ONNX Runtime (experimental)")
        print("  6. MLX (Apple Silicon, experimental)")
        print("  7. Custom engine")

        # Suggest best default based on availability
        if ollama_available:
            default_choice = "1"
            suggestion = " (llama.cpp recommended - local GGUF models detected)"
        elif hf_authenticated:
            default_choice = "2"
            suggestion = " (PyTorch recommended)"
        else:
            default_choice = "1"
            suggestion = " (llama.cpp recommended)"

        engine_choice = prompts.get_user_input(
            f"Select engine (1-7, default: {default_choice}){suggestion}",
            valid_choices=["1", "2", "3", "4", "5", "6", "7", ""],
            allow_empty=True
        )

        engine_map = {
            "1": "llamacpp",
            "2": "pytorch",
            "3": "tensorflow",
            "4": "jax",
            "5": "onnx",
            "6": "mlx"
        }

        # Set smart default
        default_engine = engine_map.get(default_choice, "llamacpp")
        engine_map[""] = default_engine

        if engine_choice == "7":
            config['engine'] = prompts.get_user_input("Enter engine name", allow_empty=False)
        else:
            config['engine'] = engine_map.get(engine_choice, default_engine)
        
        # Model selection using the new catalog
        print(f"\n📚 Select Model for {config['engine'].upper()} engine:")
        
        selector = ModelSelector(config['engine'])
        selected_model = selector.select_model()
        
        if selected_model is None:
            # User cancelled
            return {}
        
        config['model'] = selected_model
        
        # Show model info if available
        model_info = get_model_info(config['engine'], selected_model)
        if model_info:
            print(f"\n📋 Model Details:")
            print(f"   Size: {model_info.size}")
            print(f"   Memory: ~{model_info.memory_estimate}")
            print(f"   Description: {model_info.description}")
            if model_info.requires_auth:
                print(f"   ⚠️  Note: Requires Hugging Face authentication")
        
        # Engine-specific configurations
        if config['engine'] == 'onnx':
            config['onnx_tokenizer'] = prompts.get_user_input(
                "\nEnter tokenizer name/path (required for ONNX)",
                allow_empty=False
            )
        elif config['engine'] == 'llamacpp':
            gpu_layers = prompts.get_user_input(
                "\nGPU layers to offload (-1 for all, default: -1)",
                allow_empty=True
            )
            if gpu_layers:
                try:
                    config['llama_cpp_n_gpu_layers'] = int(gpu_layers)
                except ValueError:
                    config['llama_cpp_n_gpu_layers'] = -1
            else:
                config['llama_cpp_n_gpu_layers'] = -1
        elif config['engine'] == 'mlx':
            adapter = prompts.get_user_input(
                "\nLoRA adapter path (optional, press Enter to skip)",
                allow_empty=True
            )
            if adapter and adapter != "":
                config['mlx_adapter_path'] = adapter
        
        return config
    
    def _quick_play_classic(self) -> Dict[str, Any]:
        """Quick play classic mode with sensible defaults."""
        print(uic.color_text("\n⚡ Quick Play Mode - Starting with defaults!", cfg.COLOR_GREEN))
        print("Using: google/gemma-2b-it (PyTorch)")
        print("Settings: 8 rounds, temperature 0.7, top-k 8, top-p 0.95")
        
        return {
            'mode': 'classic',
            'tutorial': False,
            'comparison': False,
            'engine': 'pytorch',
            'model': 'google/gemma-2b-it',
            'steps': 8,
            'temperature': 0.7,
            'top_k': 8,
            'top_p': 0.95,
            'show_attention': True,
            'num_choices': 4,
            'permutation_length': 1,
            'focus_words': False,
            'player_choice_mode': False,
            'verbose': False,
            'load_in_4bit': False,
            'load_in_8bit': False,
            'use_kv_cache': True
        }
    
    def _quick_play_tutorial(self) -> Dict[str, Any]:
        """Quick tutorial mode with defaults."""
        print(uic.color_text("\n🎓 Quick Tutorial - Starting learning mode!", cfg.COLOR_GREEN))
        print("Using: google/gemma-2b-it for demonstrations")
        
        return {
            'mode': 'tutorial',
            'tutorial': True,
            'comparison': False,
            'engine': 'pytorch',
            'model': 'google/gemma-2b-it',
            'temperature': 0.7,
            'top_k': 8,
            'top_p': 0.95,
            'steps': 5,
            'verbose': True,
            'show_attention': True,
            'load_in_4bit': False,
            'use_kv_cache': True
        }
    
    def _quick_play_comparison(self) -> Dict[str, Any]:
        """Quick comparison mode with 2 small models."""
        print(uic.color_text("\n🔬 Quick Compare - Setting up 2 models!", cfg.COLOR_GREEN))
        print("Comparing:")
        print("  • google/gemma-2b-it")
        print("  • google/gemma-2-2b-it")
        
        return {
            'mode': 'comparison',
            'tutorial': False,
            'comparison': True,
            'comparison_models': [
                'pytorch:google/gemma-2b-it',
                'pytorch:google/gemma-2-2b-it'
            ],
            'steps': 8,
            'temperature': 0.7,
            'top_k': 8,
            'top_p': 0.95,
            'show_attention': True,
            'player_choice_mode': False,
            'verbose': False,
            'load_in_4bit': False,
            'use_kv_cache': True
        }
    
    def apply_config_to_args(self, args, config: Dict[str, Any]) -> None:
        """Apply interactive configuration to args namespace."""
        for key, value in config.items():
            # Skip mode indicator
            if key == 'mode':
                continue
            # Handle special case for comparison models
            if key == 'comparison_models' and value:
                setattr(args, key, value)
            else:
                setattr(args, key, value)

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available and has models."""
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True, timeout=5)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            return len([l for l in lines if l.strip()]) > 0
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _check_huggingface_auth(self) -> bool:
        """Check if HuggingFace authentication is available."""
        try:
            import os
            from pathlib import Path

            # Check for token in environment variable
            if os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN'):
                return True

            # Check for token in HF cache
            hf_token_path = Path.home() / '.cache' / 'huggingface' / 'token'
            if hf_token_path.exists():
                return True

            # Check for token in new location
            hf_token_path_new = Path.home() / '.huggingface' / 'token'
            if hf_token_path_new.exists():
                return True

            return False
        except Exception:
            return False
