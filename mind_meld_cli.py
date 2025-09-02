#!/usr/bin/env python3
"""
Mind Meld CLI - Standalone interface for Mind Meld mode
Allows melding multiple LLM models with various swap strategies and configurations.
"""

import argparse
import sys
import os
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.engine_interface import LLMEngine
from src.core import ui, config as cfg
from src.core.mind_meld_mode import MindMeldMode
from src.mind_meld.core.config import SwapStrategy, TranslationMode, VocabularyStrategy
from src.engines.engine_factory import get_engine, SUPPORTED_ENGINES


@dataclass
class MindMeldConfig:
    """Configuration for Mind Meld session"""
    models: List[Tuple[str, str]] = field(default_factory=list)  # [(engine, model_name), ...]
    swap_strategy: SwapStrategy = SwapStrategy.PATTERN_BASED
    translation_mode: TranslationMode = TranslationMode.INTERSECTION
    vocabulary_strategy: VocabularyStrategy = VocabularyStrategy.RESTRICT_TO_INTERSECTION
    
    # Generation parameters
    temperature: float = 0.7
    top_k: int = 8
    top_p: float = 0.95
    steps: int = 20
    
    # Swap strategy specific settings
    fixed_interval: int = 5  # For FIXED_INTERVAL strategy
    confidence_threshold: float = 0.5  # For CONFIDENCE_BASED strategy
    
    # Display options
    verbose: bool = False
    show_attention: bool = True
    initial_prompt: str = "In a world where two minds are better than one,"


class MindMeldCLI:
    """Interactive CLI for Mind Meld mode"""
    
    # Popular model combinations
    PRESETS = {
        "gemma_small": [
            ("pytorch", "google/gemma-3-1b-it"),
            ("pytorch", "google/gemma-2-2b-it")
        ],
        "gemma_mixed": [
            ("pytorch", "google/gemma-3-1b-it"),
            ("pytorch", "google/gemma-2-2b-it"),
            ("pytorch", "google/gemma-2b-it")
        ],
        "gemma_2b_variants": [
            ("pytorch", "google/gemma-2b"),
            ("pytorch", "google/gemma-2b-it")
        ],
        "gemma3_family": [
            ("pytorch", "google/gemma-3-1b"),
            ("pytorch", "google/gemma-3-1b-it")
        ]
    }
    
    def __init__(self):
        self.config = MindMeldConfig()
        
    def print_header(self):
        """Print the Mind Meld CLI header"""
        print("=" * 70)
        print(ui.color_text("🧠 Mind Meld CLI - Multi-Model Neural State Transfer 🧠", cfg.COLOR_CYAN))
        print("=" * 70)
        print("Meld multiple LLM models together during text generation.")
        print("Watch as models swap their internal states mid-sentence!\n")
    
    def show_main_menu(self) -> Optional[MindMeldConfig]:
        """Show the main interactive menu"""
        self.print_header()
        
        print("Select mode:")
        print("  1. Quick Start (Gemma-3 1B + Gemma-2 2B)")
        print("  2. Popular Combinations")
        print("  3. Custom Model Selection")
        print("  4. Load from Previous Config")
        print("  5. Exit")
        
        choice = input("\nYour choice (1-5): ").strip()
        
        if choice == "1":
            return self.quick_start()
        elif choice == "2":
            return self.select_preset()
        elif choice == "3":
            return self.custom_setup()
        elif choice == "4":
            print(ui.color_text("Config loading not yet implemented", cfg.COLOR_YELLOW))
            return self.show_main_menu()
        elif choice == "5":
            return None
        else:
            print(ui.color_text("Invalid choice. Please try again.", cfg.COLOR_RED))
            return self.show_main_menu()
    
    def quick_start(self) -> MindMeldConfig:
        """Quick start with default Gemma models"""
        print(ui.color_text("\n⚡ Quick Start Mode", cfg.COLOR_CYAN))
        print("Using: Gemma-3 1B + Gemma-2 2B")
        
        self.config.models = self.PRESETS["gemma_small"]
        self.configure_swap_strategy()
        self.configure_generation_params()
        
        return self.config
    
    def select_preset(self) -> MindMeldConfig:
        """Select from popular model combinations"""
        print(ui.color_text("\n📚 Popular Combinations", cfg.COLOR_CYAN))
        
        presets_list = list(self.PRESETS.keys())
        for i, preset_name in enumerate(presets_list, 1):
            models = self.PRESETS[preset_name]
            model_names = [m[1].split('/')[-1] for _, m in models]
            print(f"  {i}. {preset_name}: {' + '.join(model_names)}")
        
        while True:
            choice = input(f"\nSelect preset (1-{len(presets_list)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(presets_list):
                    preset_name = presets_list[idx]
                    self.config.models = self.PRESETS[preset_name]
                    print(f"Selected: {preset_name}")
                    break
                else:
                    print(ui.color_text("Invalid selection", cfg.COLOR_RED))
            except ValueError:
                print(ui.color_text("Please enter a number", cfg.COLOR_RED))
        
        self.configure_swap_strategy()
        self.configure_generation_params()
        
        return self.config
    
    def custom_setup(self) -> MindMeldConfig:
        """Custom model selection and configuration"""
        print(ui.color_text("\n🔧 Custom Setup", cfg.COLOR_CYAN))
        
        # Select number of models
        while True:
            num_models = input("How many models to meld? (2-5): ").strip()
            try:
                n = int(num_models)
                if 2 <= n <= 5:
                    break
                else:
                    print(ui.color_text("Please enter a number between 2 and 5", cfg.COLOR_RED))
            except ValueError:
                print(ui.color_text("Please enter a valid number", cfg.COLOR_RED))
        
        # Select each model
        self.config.models = []
        for i in range(n):
            print(f"\n--- Model {i+1} ---")
            engine, model = self.select_single_model()
            self.config.models.append((engine, model))
        
        self.configure_swap_strategy()
        self.configure_generation_params()
        
        return self.config
    
    def select_single_model(self) -> Tuple[str, str]:
        """Select a single model with engine type"""
        # Select engine
        print("Available engines:")
        engines = list(SUPPORTED_ENGINES)
        for i, engine in enumerate(engines, 1):
            print(f"  {i}. {engine}")
        
        while True:
            engine_choice = input(f"Select engine (1-{len(engines)}) [1]: ").strip() or "1"
            try:
                idx = int(engine_choice) - 1
                if 0 <= idx < len(engines):
                    engine = engines[idx]
                    break
                else:
                    print(ui.color_text("Invalid selection", cfg.COLOR_RED))
            except ValueError:
                print(ui.color_text("Please enter a number", cfg.COLOR_RED))
        
        # Select model
        if engine == "pytorch":
            print("\nCommon PyTorch models:")
            print("  1. google/gemma-3-1b-it")
            print("  2. google/gemma-3-1b")
            print("  3. google/gemma-2-2b-it")
            print("  4. google/gemma-2b-it")
            print("  5. google/gemma-2b")
            print("  6. Custom (enter path)")
            
            model_choice = input("Select model (1-6): ").strip()
            
            model_map = {
                "1": "google/gemma-3-1b-it",
                "2": "google/gemma-3-1b",
                "3": "google/gemma-2-2b-it",
                "4": "google/gemma-2b-it",
                "5": "google/gemma-2b",
            }
            
            if model_choice in model_map:
                model = model_map[model_choice]
            elif model_choice == "6":
                model = input("Enter model path/name: ").strip()
            else:
                print("Invalid choice, using default")
                model = "google/gemma-3-1b-it"
        else:
            model = input(f"Enter {engine} model path: ").strip()
        
        print(f"Selected: {engine}:{model}")
        return engine, model
    
    def configure_swap_strategy(self):
        """Configure the model swap strategy"""
        print(ui.color_text("\n🔄 Swap Strategy Configuration", cfg.COLOR_CYAN))
        
        strategies = [
            (SwapStrategy.PATTERN_BASED, "Pattern-based (swap on punctuation)"),
            (SwapStrategy.FIXED_INTERVAL, f"Fixed interval (every N tokens)"),
            (SwapStrategy.ROUND_ROBIN, "Round-robin (rotate in order)"),
            (SwapStrategy.CONFIDENCE_BASED, "Confidence-based (swap on low confidence)"),
            (SwapStrategy.RANDOM, "Random swapping"),
            (SwapStrategy.ATTENTION_GUIDED, "Attention-guided"),
        ]
        
        print("Available strategies:")
        for i, (_, desc) in enumerate(strategies, 1):
            print(f"  {i}. {desc}")
        
        choice = input("\nSelect strategy (1-6) [1]: ").strip() or "1"
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(strategies):
                self.config.swap_strategy = strategies[idx][0]
                
                # Additional configuration for specific strategies
                if self.config.swap_strategy == SwapStrategy.FIXED_INTERVAL:
                    interval = input("Swap interval (tokens) [5]: ").strip() or "5"
                    self.config.fixed_interval = int(interval)
                elif self.config.swap_strategy == SwapStrategy.CONFIDENCE_BASED:
                    threshold = input("Confidence threshold (0-1) [0.5]: ").strip() or "0.5"
                    self.config.confidence_threshold = float(threshold)
            else:
                print("Invalid choice, using pattern-based")
                self.config.swap_strategy = SwapStrategy.PATTERN_BASED
        except ValueError:
            print("Invalid input, using pattern-based")
            self.config.swap_strategy = SwapStrategy.PATTERN_BASED
    
    def configure_generation_params(self):
        """Configure generation parameters"""
        print(ui.color_text("\n⚙️ Generation Parameters", cfg.COLOR_CYAN))
        
        # Temperature
        temp = input(f"Temperature (0.1-2.0) [{self.config.temperature}]: ").strip()
        if temp:
            try:
                self.config.temperature = float(temp)
            except ValueError:
                print("Invalid temperature, using default")
        
        # Top-K
        topk = input(f"Top-K (1-100) [{self.config.top_k}]: ").strip()
        if topk:
            try:
                self.config.top_k = int(topk)
            except ValueError:
                print("Invalid top-k, using default")
        
        # Top-P
        topp = input(f"Top-P (0.1-1.0) [{self.config.top_p}]: ").strip()
        if topp:
            try:
                self.config.top_p = float(topp)
            except ValueError:
                print("Invalid top-p, using default")
        
        # Steps
        steps = input(f"Number of generation steps [{self.config.steps}]: ").strip()
        if steps:
            try:
                self.config.steps = int(steps)
            except ValueError:
                print("Invalid steps, using default")
        
        # Initial prompt
        print(f"\nCurrent prompt: '{self.config.initial_prompt}'")
        new_prompt = input("Enter new prompt (or press Enter to keep): ").strip()
        if new_prompt:
            self.config.initial_prompt = new_prompt
        
        # Verbose mode
        verbose = input("\nEnable verbose mode? (y/n) [n]: ").strip().lower()
        self.config.verbose = verbose == 'y'
    
    def load_models(self, config: MindMeldConfig) -> List[LLMEngine]:
        """Load the specified models"""
        loaded_engines = []
        
        for engine_type, model_name in config.models:
            print(ui.color_text(f"\n📦 Loading {model_name} with {engine_type} engine...", cfg.COLOR_CYAN))
            
            try:
                # Create args namespace for engine initialization
                engine_args = argparse.Namespace(
                    engine=engine_type,
                    model=model_name,
                    temperature=config.temperature,
                    top_k=config.top_k,
                    top_p=config.top_p,
                    steps=config.steps,
                    verbose=config.verbose,
                    show_attention=config.show_attention,
                    # Add other necessary args
                    pytorch_device_map="auto",
                    use_kv_cache=True,
                    onnx_tokenizer=None,
                )
                
                # Initialize engine
                engine = get_engine(
                    engine_type,
                    model_name,
                    vars(engine_args)
                )
                
                print("Loading model...")
                engine.load()
                print(ui.color_text("✓ Model loaded successfully!", cfg.COLOR_GREEN))
                
                loaded_engines.append(engine)
                
            except Exception as e:
                print(ui.color_text(f"✗ Failed to load {model_name}: {e}", cfg.COLOR_RED))
                
                # Ask whether to continue
                if loaded_engines:
                    cont = input("Continue with loaded models? (y/n): ").strip().lower()
                    if cont != 'y':
                        return []
        
        return loaded_engines
    
    def run_mind_meld(self, config: MindMeldConfig, engines: List[LLMEngine]):
        """Run the Mind Meld session"""
        print(ui.color_text("\n🚀 Starting Mind Meld Session", cfg.COLOR_GREEN))
        if config.use_enhanced:
            print(ui.color_text("🎆 Enhanced Mode Active", cfg.COLOR_YELLOW))
        print("=" * 70)
        
        # Create args for MindMeldMode
        meld_args = argparse.Namespace(
            temperature=config.temperature,
            top_k=config.top_k,
            top_p=config.top_p,
            steps=config.steps,
            verbose=config.verbose,
            show_attention=config.show_attention,
            swap_strategy=config.swap_strategy,
            fixed_interval=config.fixed_interval,
            confidence_threshold=config.confidence_threshold,
            initial_prompt=config.initial_prompt,
            # Enhanced features
            use_enhanced=config.use_enhanced,
            use_blending=config.use_blending,
            blend_strategy=config.blend_strategy,
            alignment_strategy=config.alignment_strategy,
            stats_file=config.stats_file,
        )
        
        # Initialize and run Mind Meld mode
        try:
            meld_mode = MindMeldMode(engines, meld_args)
            meld_mode.run()
        except KeyboardInterrupt:
            print(ui.color_text("\n\n🛑 Mind Meld interrupted by user", cfg.COLOR_YELLOW))
        except Exception as e:
            print(ui.color_text(f"\n\n❌ Error during Mind Meld: {e}", cfg.COLOR_RED))
            if config.verbose:
                import traceback
                traceback.print_exc()
    
    def parse_cli_args(self) -> argparse.Namespace:
        """Parse command-line arguments"""
        parser = argparse.ArgumentParser(
            description="Mind Meld CLI - Meld multiple LLM models during generation",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument(
            "--models",
            nargs="+",
            help="Models to meld (format: engine:model_name or just model_name for pytorch)"
        )
        
        parser.add_argument(
            "--strategy",
            choices=["pattern", "fixed", "roundrobin", "confidence", "random", "attention"],
            default="pattern",
            help="Swap strategy to use"
        )
        
        parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation")
        parser.add_argument("--top-k", type=int, default=8, help="Top-K for generation")
        parser.add_argument("--top-p", type=float, default=0.95, help="Top-P for generation")
        parser.add_argument("--steps", type=int, default=20, help="Number of generation steps")
        
        parser.add_argument("--interval", type=int, default=5, help="Swap interval for fixed strategy")
        parser.add_argument("--threshold", type=float, default=0.5, help="Confidence threshold")
        
        # Enhanced features
        parser.add_argument("--enhanced", action="store_true", help="Enable enhanced features")
        parser.add_argument("--blend", action="store_true", help="Use logit blending")
        parser.add_argument(
            "--blend-strategy",
            choices=["weighted_average", "confidence_weighted", "dynamic_weighted", "ensemble_voting"],
            default="weighted_average",
            help="Blending strategy"
        )
        parser.add_argument(
            "--alignment",
            choices=["hybrid", "intersection", "fuzzy", "subword", "semantic"],
            default="hybrid",
            help="Vocabulary alignment strategy"
        )
        parser.add_argument("--stats-file", type=str, help="Save statistics to file")
        
        parser.add_argument("--prompt", type=str, help="Initial prompt for generation")
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        parser.add_argument("--no-attention", action="store_true", help="Disable attention visualization")
        
        return parser.parse_args()
    
    def run_from_cli(self, args: argparse.Namespace):
        """Run Mind Meld from CLI arguments"""
        config = MindMeldConfig()
        
        # Parse models
        if args.models:
            config.models = []
            for model_spec in args.models:
                if ":" in model_spec:
                    engine, model = model_spec.split(":", 1)
                else:
                    engine = "pytorch"
                    model = model_spec
                config.models.append((engine, model))
        else:
            # Use default if no models specified
            config.models = self.PRESETS["gemma_small"]
        
        # Set strategy
        strategy_map = {
            "pattern": SwapStrategy.PATTERN_BASED,
            "fixed": SwapStrategy.FIXED_INTERVAL,
            "roundrobin": SwapStrategy.ROUND_ROBIN,
            "confidence": SwapStrategy.CONFIDENCE_BASED,
            "random": SwapStrategy.RANDOM,
            "attention": SwapStrategy.ATTENTION_GUIDED,
        }
        config.swap_strategy = strategy_map.get(args.strategy, SwapStrategy.PATTERN_BASED)
        
        # Set generation parameters
        config.temperature = args.temperature
        config.top_k = args.top_k
        config.top_p = args.top_p
        config.steps = args.steps
        config.fixed_interval = args.interval
        config.confidence_threshold = args.threshold
        
        # Enhanced features
        config.use_enhanced = args.enhanced
        config.use_blending = args.blend
        config.blend_strategy = args.blend_strategy
        config.alignment_strategy = args.alignment
        config.stats_file = args.stats_file
        
        if args.prompt:
            config.initial_prompt = args.prompt
        
        config.verbose = args.verbose
        config.show_attention = not args.no_attention
        
        # Load models and run
        engines = self.load_models(config)
        if engines and len(engines) >= 2:
            self.run_mind_meld(config, engines)
        else:
            print(ui.color_text("Failed to load sufficient models for Mind Meld", cfg.COLOR_RED))


def main():
    """Main entry point"""
    cli = MindMeldCLI()
    
    # Check if CLI arguments were provided
    if len(sys.argv) > 1:
        # CLI mode
        args = cli.parse_cli_args()
        cli.run_from_cli(args)
    else:
        # Interactive mode
        config = cli.show_main_menu()
        
        if config:
            print(ui.color_text("\n📋 Configuration Summary:", cfg.COLOR_CYAN))
            print(f"  Models: {len(config.models)}")
            for i, (engine, model) in enumerate(config.models, 1):
                print(f"    {i}. {model} ({engine})")
            print(f"  Strategy: {config.swap_strategy.value}")
            print(f"  Temperature: {config.temperature}")
            print(f"  Top-K: {config.top_k}")
            print(f"  Top-P: {config.top_p}")
            print(f"  Steps: {config.steps}")
            
            confirm = input("\nProceed with this configuration? (y/n): ").strip().lower()
            
            if confirm == 'y':
                engines = cli.load_models(config)
                if engines and len(engines) >= 2:
                    cli.run_mind_meld(config, engines)
                else:
                    print(ui.color_text("Failed to load sufficient models for Mind Meld", cfg.COLOR_RED))
            else:
                print(ui.color_text("Configuration cancelled", cfg.COLOR_YELLOW))
        else:
            print(ui.color_text("\nExiting Mind Meld CLI", cfg.COLOR_YELLOW))


if __name__ == "__main__":
    main()