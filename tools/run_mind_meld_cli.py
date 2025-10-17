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

# Add project root to the path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine_interface import LLMEngine
from src.ui import displays as ui
from src.core import config as cfg
from src.mind_meld.mode import MindMeldMode
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
    
    # Enhanced features
    use_enhanced: bool = False
    use_blending: bool = False
    use_weighted_average: bool = False
    use_abe: bool = False  # Agreement-Based Ensembling
    use_stats_tracker: bool = False
    blend_strategy: str = "weighted_average"
    alignment_strategy: str = "semantic"
    stats_file: Optional[str] = None


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
        
    def parse_cli_args(self) -> argparse.Namespace:
        """Parse command-line arguments for direct CLI usage."""
        parser = argparse.ArgumentParser(
            description="Mind Meld CLI - meld multiple LLMs together"
        )

        parser.add_argument(
            "--models",
            type=str,
            nargs="+",
            help="Models to meld (format: engine:model or model to default to PyTorch)",
        )
        parser.add_argument(
            "--strategy",
            type=str,
            default="pattern",
            choices=["pattern", "fixed", "fixed_interval", "round_robin", "random"],
            help="Swap strategy to control when models take over"
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Token interval for fixed swap strategy"
        )
        parser.add_argument(
            "--temperature",
            type=float,
            default=0.7,
            help="Generation temperature"
        )
        parser.add_argument(
            "--top-k",
            type=int,
            default=8,
            help="Top-K sampling limit"
        )
        parser.add_argument(
            "--top-p",
            type=float,
            default=0.95,
            help="Top-P (nucleus) sampling threshold"
        )
        parser.add_argument(
            "--steps",
            type=int,
            default=20,
            help="Number of generation steps"
        )
        parser.add_argument(
            "--prompt",
            type=str,
            default=None,
            help="Initial prompt to start the meld"
        )
        parser.add_argument(
            "--use-weighted-average",
            action="store_true",
            help="Use weighted average ensemble across models"
        )
        parser.add_argument(
            "--use-abe",
            action="store_true",
            help="Enable Agreement-Based Ensembling"
        )
        parser.add_argument(
            "--use-blending",
            action="store_true",
            help="Blend logits from all models instead of single-source swaps"
        )
        parser.add_argument(
            "--blend-strategy",
            type=str,
            default="weighted_average",
            choices=[
                "weighted_average",
                "confidence_weighted",
                "dynamic_weighted",
                "attention_weighted",
                "learned",
                "hierarchical",
                "ensemble_voting"
            ],
            help="Blending strategy to use when --use-blending is enabled"
        )
        parser.add_argument(
            "--alignment",
            type=str,
            default="semantic",
            help="Vocabulary alignment strategy"
        )
        parser.add_argument(
            "--use-enhanced",
            action="store_true",
            help="Enable enhanced Mind Meld features"
        )
        parser.add_argument(
            "--use-stats-tracker",
            action="store_true",
            help="Track statistics for each model during the session"
        )
        parser.add_argument(
            "--stats-file",
            type=str,
            default=None,
            help="Optional path to write statistics JSON"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--show-attention",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Toggle attention heatmap display"
        )

        return parser.parse_args()

    def _strategy_from_string(self, value: str) -> SwapStrategy:
        """Convert string input to SwapStrategy enum."""
        value_normalized = (value or "pattern").lower()
        mapping = {
            "pattern": SwapStrategy.PATTERN_BASED,
            "pattern_based": SwapStrategy.PATTERN_BASED,
            "fixed": SwapStrategy.FIXED_INTERVAL,
            "fixed_interval": SwapStrategy.FIXED_INTERVAL,
            "round_robin": SwapStrategy.ROUND_ROBIN,
            "random": SwapStrategy.RANDOM,
        }
        return mapping.get(value_normalized, SwapStrategy.PATTERN_BASED)

    def run_from_cli(self, args: argparse.Namespace) -> None:
        """Run Mind Meld session using parsed CLI arguments."""
        config = MindMeldConfig()

        if not args.models or len(args.models) < 2:
            print(ui.color_text("Mind Meld CLI requires at least two models specified with --models", cfg.COLOR_RED))
            return

        config.models = []
        for spec in args.models:
            if ":" in spec:
                engine, model_name = spec.split(":", 1)
            else:
                engine = "pytorch"
                model_name = spec
            config.models.append((engine, model_name))

        config.swap_strategy = self._strategy_from_string(args.strategy)
        config.fixed_interval = args.interval
        config.temperature = args.temperature
        config.top_k = args.top_k
        config.top_p = args.top_p
        config.steps = args.steps
        config.initial_prompt = args.prompt or self.config.initial_prompt
        config.verbose = args.verbose
        config.show_attention = args.show_attention
        config.use_weighted_average = args.use_weighted_average
        config.use_abe = args.use_abe
        config.use_blending = args.use_blending
        config.blend_strategy = args.blend_strategy
        config.alignment_strategy = args.alignment
        config.use_enhanced = args.use_enhanced
        config.use_stats_tracker = args.use_stats_tracker
        config.stats_file = args.stats_file

        engines = self.load_models(config)
        if not engines or len(engines) < 2:
            print(ui.color_text("Failed to load sufficient models for Mind Meld", cfg.COLOR_RED))
            return

        self.run_mind_meld(config, engines)

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
        
        # Ensemble method selection
        print("\nEnsemble method:")
        print("  1. None (models take turns)")
        print("  2. Weighted averaging (blend all model probabilities)")
        print("  3. ABE (Agreement-Based Ensembling)")
        
        ensemble = input("Select ensemble method (1-3) [1]: ").strip() or "1"
        
        if ensemble == "2":
            self.config.use_weighted_average = True
            print("✓ Weighted averaging enabled - all models will contribute to each token")
        elif ensemble == "3":
            self.config.use_abe = True
            print("✓ ABE enabled - models must agree on token choices")
        else:
            self.config.use_weighted_average = False
            self.config.use_abe = False
    
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
            use_weighted_average=config.use_weighted_average,
            use_abe=config.use_abe,
            blend_strategy=config.blend_strategy,
            alignment_strategy=config.alignment_strategy,
            use_stats_tracker=config.use_stats_tracker,
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
