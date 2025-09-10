#!/usr/bin/env python3
"""
GAMMA - Game Analyzing Model Methods Attentively
Main entry point for the interactive LLM guessing game.
Main entry point for the interactive LLM guessing game.
"""

import argparse
import sys
import time
import random
from typing import Optional, List, Tuple, Set, Dict, Any, Union

sys.path.insert(0, 'src')

from core import config as cfg
from core import ui
from core import game_logic
from core import explanations
from engines.engine_factory import get_engine, SUPPORTED_ENGINES
from core.engine_interface import LLMEngine
from core.tutorial_mode import TutorialMode
from core.comparison_mode import ComparisonMode
from core.interactive_menu import InteractiveMenu


# Global for tracking explained tokens in focus mode
PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE: Set[Union[int, str]] = set()


def _concatenate_tensors(tensor1: Any, tensor2: Any, dim: int = -1, engine: Optional[LLMEngine] = None) -> Optional[Any]:
    """Concatenate tensors/arrays using engine abstraction when available."""
    if tensor1 is None: return tensor2
    if tensor2 is None: return tensor1

    # If engine is provided, use its abstraction
    if engine is not None:
        try:
            return engine.concatenate_tensors(tensor1, tensor2, dim=dim)
        except Exception as e:
            print(f"Warning: Failed to concatenate using engine abstraction: {e}")
    
    # Fallback for lists
    if isinstance(tensor1, list) and isinstance(tensor2, list):
        return tensor1 + tensor2
    
    print(f"Warning: Could not concatenate tensors of types ({type(tensor1)}, {type(tensor2)})")
    return None


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GAMMA: Interactive LLM Guessing Game - Test your intuition against language models!\n\nRun without arguments for interactive configuration.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=True
    )
    
    # Core arguments
    parser.add_argument("--engine", type=str, choices=SUPPORTED_ENGINES, default="pytorch",
                        help="LLM engine to use (pytorch recommended for Gemma models)")
    parser.add_argument("--model", type=str, default=None,
                        help="Model ID (HF name/local path). Interactive selection if omitted.")
    
    # Game parameters
    parser.add_argument("--steps", type=int, default=cfg.DEFAULT_MAX_DECODE_STEPS,
                        help="Maximum game rounds")
    parser.add_argument("--temperature", type=float, default=cfg.DEFAULT_TEMPERATURE,
                        help="Sampling temperature (lower = more focused)")
    parser.add_argument("--top-k", type=int, default=cfg.DEFAULT_TOP_K,
                        help="Top-K filtering (limits vocabulary)")
    parser.add_argument("--top-p", type=float, default=cfg.DEFAULT_TOP_P,
                        help="Top-P (nucleus) filtering")
    parser.add_argument("--num-choices", type=int, default=cfg.DEFAULT_NUM_CHOICES,
                        help="Number of choices presented per round")
    parser.add_argument("--permutation-length", type=int, default=cfg.DEFAULT_PERMUTATION_LENGTH,
                        help="Number of tokens per choice (default: 1)")
    
    # Game modes
    parser.add_argument("--focus-words", action="store_true", default=cfg.DEFAULT_FOCUS_WORDS,
                        help="Prioritize 'word' tokens in choices")
    parser.add_argument("--player-choice-mode", action="store_true", default=False,
                        help="EXPERIMENTAL: Player's correct full guess drives generation")
    parser.add_argument("--allow-eos-continue", action="store_true", default=False,
                        help="Offer to continue generating after max_steps if EOS not hit")
    parser.add_argument("--tutorial", action="store_true", default=False,
                        help="Run interactive tutorial mode to learn LLM concepts")
    parser.add_argument("--comparison", action="store_true", default=False,
                        help="Compare predictions from multiple models side-by-side")
    parser.add_argument("--comparison-models", type=str, nargs="+", default=None,
                        help="Models to compare (format: engine:model_name)")
    parser.add_argument("--chat", action="store_true", default=False,
                        help="Enable simple, direct chat mode.")
    parser.add_argument("--prompt", type=str, default=None,
                        help="Run single-shot inference with the given prompt.")
    
    # Display options
    parser.add_argument("--show-attention", action=argparse.BooleanOptionalAction, 
                        default=cfg.DEFAULT_SHOW_ATTENTION,
                        help="Show attention visualization heatmap")
    parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, 
                        default=cfg.DEFAULT_VERBOSE,
                        help="Enable detailed explanations")
    parser.add_argument("--no-color", action="store_true", default=not cfg.USE_COLORS,
                        help="Disable terminal colors")
    
    # Model/Engine configuration
    parser.add_argument("--seed", type=int, default=0,
                        help="Random seed for reproducibility")
    parser.add_argument("--hf-token", type=str, default=None,
                        help="Hugging Face Hub token for gated models")
    parser.add_argument("--trust-remote-code", action="store_true", default=False,
                        help="Trust remote code for Hugging Face models")
    
    # PyTorch Engine specific
    pt_group = parser.add_argument_group("PyTorch Engine Options")
    pt_group.add_argument("--load-in-4bit", action="store_true",
                          help="PyTorch: 4-bit quantization (reduces memory usage)")
    pt_group.add_argument("--bnb-4bit-quant-type", type=str, default="nf4",
                          help="PyTorch 4-bit: Quantization type")
    pt_group.add_argument("--bnb-4bit-compute-dtype", type=str, default="bfloat16",
                          help="PyTorch 4-bit: Compute dtype")
    pt_group.add_argument("--bnb-4bit-use-double-quant", action="store_true",
                          help="PyTorch 4-bit: Use double quantization")
    pt_group.add_argument("--load-in-8bit", action="store_true",
                          help="PyTorch: 8-bit quantization")
    pt_group.add_argument("--pytorch-attn", type=str, default=cfg.PYTORCH_ATTN_IMPLEMENTATION,
                          choices=["eager", "sdpa", "flash_attention_2"],
                          help="PyTorch: Attention implementation")
    pt_group.add_argument("--pytorch-device-map", type=str, default=cfg.PYTORCH_DEVICE_MAP,
                          help="PyTorch: Device map (e.g., 'auto', 'cpu', 'cuda:0')")
    pt_group.add_argument("--use-kv-cache", action=argparse.BooleanOptionalAction, 
                          default=cfg.PYTORCH_USE_KV_CACHE,
                          help="PyTorch/TF: Use KV cache during generation")
    pt_group.add_argument("--low-cpu-mem-usage", action=argparse.BooleanOptionalAction, 
                          default=True,
                          help="PyTorch: Reduce CPU RAM during model loading")
    
    # Other engines (for future compatibility)
    lc_group = parser.add_argument_group("Llama.cpp Engine Options")
    lc_group.add_argument("--llama-cpp-n-gpu-layers", type=int, default=cfg.LLAMA_CPP_N_GPU_LAYERS,
                          help="Llama.cpp: GPU layers (-1 for all)")
    lc_group.add_argument("--llama-cpp-n-ctx", type=int, default=cfg.LLAMA_CPP_N_CTX,
                          help="Llama.cpp: Context size")
    lc_group.add_argument("--llama-cpp-lib-verbose", action="store_true", 
                          default=cfg.LLAMA_CPP_LIB_VERBOSE,
                          help="Llama.cpp: Library's internal verbose output")
    
    onnx_group = parser.add_argument_group("ONNX Runtime Engine Options")
    onnx_group.add_argument("--onnx-tokenizer", type=str, default=None,
                            help="ONNX: Required. HF tokenizer name/path")
    onnx_group.add_argument("--onnx-providers", type=str, nargs="+", 
                            default=cfg.ONNX_PROVIDERS,
                            help=f"ONNX: Execution providers")
    
    jax_group = parser.add_argument_group("JAX Engine Options")
    jax_group.add_argument("--jax-dtype", type=str, default=cfg.JAX_DTYPE,
                           choices=["float32", "bfloat16", "float16"],
                           help="JAX: Model data type")
    
    mlx_group = parser.add_argument_group("MLX Engine Options")
    mlx_group.add_argument("--mlx-adapter-path", type=str, default=None,
                           help="MLX: Path to LoRA adapter")
    
    parsed_args = parser.parse_args()
    
    # Handle color settings
    if parsed_args.no_color:
        cfg.USE_COLORS = False
        for color_attr in [attr for attr in dir(cfg) if attr.startswith("COLOR_")]:
            setattr(cfg, color_attr, "")
    
    return parsed_args


def initialize_game_engine(args: argparse.Namespace) -> Optional[LLMEngine]:
    """Initialize the selected LLM engine with the specified model."""
    s_eng_name: Optional[str] = args.engine
    s_model_id: Optional[str] = args.model
    
    # Interactive engine selection if not specified
    if not s_eng_name:
        selected_engine = ui.select_engine_interactively(cfg.DEFAULT_ENGINE)
        if selected_engine is None:
            return None
        args.engine = selected_engine
        s_eng_name = args.engine
    
    # Interactive model selection if not specified
    if not s_model_id:
        if s_eng_name == "onnx" and not args.onnx_tokenizer:
            args.onnx_tokenizer = ui.get_user_input(
                "Enter HF tokenizer for ONNX model (required)",
                allow_empty=False,
                allow_quit=True
            )
            if args.onnx_tokenizer == cfg.SHORTCUT_QUIT:
                return None
        
        # Set default model for prompt
        default_model_for_prompt: Optional[str] = None
        if s_eng_name == "pytorch":
            default_model_for_prompt = cfg.DEFAULT_MODEL_NAME
        elif s_eng_name not in ["llamacpp", "onnx"]:
            default_model_for_prompt = cfg.DEFAULT_MODEL_NAME
        
        selected_model_from_ui = ui.select_model_interactively(s_eng_name, default_model_for_prompt)
        if selected_model_from_ui is None:
            return None
        args.model = selected_model_from_ui
        s_model_id = args.model
    
    # Validate ONNX requirements
    if args.engine == "onnx" and not args.onnx_tokenizer:
        print(ui.color_text(
            f"Critical: ONNX engine needs --onnx-tokenizer for model '{args.model}'.",
            cfg.COLOR_RED
        ))
        return None
    
    # Initialize the engine
    try:
        engine = get_engine(
            args.engine,
            args.model,
            vars(args)  # Pass all args as config dict
        )
        print(ui.color_text("\nLoading model... This may take a moment.", cfg.COLOR_CYAN))
        engine.load()
        print(ui.color_text("✓ Model loaded successfully!", cfg.COLOR_GREEN))
        
        # Display engine configuration summary
        engine_summary = engine.get_config_summary()
        if engine_summary:
            print("\nEngine Configuration:")
            for key, value in engine_summary.items():
                print(f"  {key}: {value}")
        
        return engine
    except Exception as e:
        print(ui.color_text(f"\n✗ Failed to initialize engine: {e}", cfg.COLOR_RED))
        return None


def run_tutorial_mode(args: argparse.Namespace) -> None:
    """Run the interactive tutorial mode."""
    print(ui.color_text("\n🎓 Starting Tutorial Mode...", cfg.COLOR_CYAN))
    
    # Initialize a default engine for demonstrations
    if not args.model:
        args.model = cfg.DEFAULT_MODEL_NAME
    
    engine = initialize_game_engine(args)
    if engine is None:
        print(ui.color_text("\nFailed to initialize engine for tutorial. Exiting.", cfg.COLOR_RED))
        return
    
    try:
        tutorial = TutorialMode(engine, args.verbose)
        tutorial.run_tutorial()
    except KeyboardInterrupt:
        print(ui.color_text("\n\nTutorial interrupted by user.", cfg.COLOR_YELLOW))
    except Exception as e:
        print(ui.color_text(f"\n\nError in tutorial: {e}", cfg.COLOR_RED))
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        print(ui.color_text("\n\nThanks for learning with GAMMA! 📚", cfg.COLOR_CYAN))


def run_comparison_mode(args: argparse.Namespace) -> None:
    """Run the model comparison mode."""
    print(ui.color_text("\n🔬 Starting Model Comparison Mode...", cfg.COLOR_CYAN))
    
    # Parse comparison models
    models_to_compare = []
    
    if args.comparison_models:
        # Parse provided models
        for model_spec in args.comparison_models:
            if ":" in model_spec:
                engine_type, model_name = model_spec.split(":", 1)
            else:
                # Default to pytorch engine
                engine_type = "pytorch"
                model_name = model_spec
            
            if engine_type not in SUPPORTED_ENGINES:
                print(ui.color_text(f"Unsupported engine: {engine_type}", cfg.COLOR_RED))
                return
            
            models_to_compare.append((engine_type, model_name))
    else:
        # Interactive selection
        print("\nSelect models to compare (at least 2):")
        print("Available options:")
        print("  1. google/gemma-2b-it (PyTorch)")
        print("  2. google/gemma-2-2b-it (PyTorch)")
        print("  3. google/gemma-2-9b-it (PyTorch)")
        print("  4. Custom model...")
        
        selected_models = []
        while len(selected_models) < 2:
            choice = ui.get_user_input(
                f"Select model {len(selected_models) + 1} (1-4 or 'done' if finished)",
                allow_quit=True
            )
            
            if choice == cfg.SHORTCUT_QUIT or choice.lower() == "done":
                if len(selected_models) >= 2:
                    break
                else:
                    print("Need at least 2 models for comparison.")
                    continue
            
            if choice == "1":
                selected_models.append(("pytorch", "google/gemma-2b-it"))
            elif choice == "2":
                selected_models.append(("pytorch", "google/gemma-2-2b-it"))
            elif choice == "3":
                selected_models.append(("pytorch", "google/gemma-2-9b-it"))
            elif choice == "4":
                engine = ui.get_user_input("Enter engine type (pytorch/tensorflow/jax/etc)")
                model = ui.get_user_input("Enter model name/path")
                selected_models.append((engine, model))
        
        models_to_compare = selected_models
    
    if len(models_to_compare) < 2:
        print(ui.color_text("Need at least 2 models for comparison mode.", cfg.COLOR_RED))
        return
    
    try:
        comparison = ComparisonMode(models_to_compare, args)
        if comparison.load_models():
            comparison.run_comparison()
        else:
            print(ui.color_text("\nFailed to load models for comparison.", cfg.COLOR_RED))
    except KeyboardInterrupt:
        print(ui.color_text("\n\nComparison interrupted by user.", cfg.COLOR_YELLOW))
    except Exception as e:
        print(ui.color_text(f"\n\nError in comparison: {e}", cfg.COLOR_RED))
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        print(ui.color_text("\n\nThanks for comparing models with GAMMA! 📊", cfg.COLOR_CYAN))

def run_meld_mode(args: argparse.Namespace) -> None:
    """Run the Mind Meld mode."""
    print(ui.color_text("\n🧠 Starting Mind Meld Mode...", cfg.COLOR_CYAN))
    
    models_to_meld = []
    if not args.meld_models or len(args.meld_models) < 2:
        print(ui.color_text("Mind Meld mode requires at least two models specified with --meld-models", cfg.COLOR_RED))
        return

    for model_spec in args.meld_models:
        if ":" in model_spec:
            engine_type, model_name = model_spec.split(":", 1)
        else:
            engine_type = "pytorch"
            model_name = model_spec
        
        if engine_type not in SUPPORTED_ENGINES:
            print(ui.color_text(f"Unsupported engine: {engine_type}", cfg.COLOR_RED))
            return
        models_to_meld.append((engine_type, model_name))

    loaded_engines = []
    for engine_type, model_name in models_to_meld:
        print(ui.color_text(f"\nLoading model {model_name} with {engine_type} engine...", cfg.COLOR_CYAN))
        engine_args = argparse.Namespace(**vars(args))
        engine_args.engine = engine_type
        engine_args.model = model_name
        engine = initialize_game_engine(engine_args)
        if engine:
            loaded_engines.append(engine)
        else:
            print(ui.color_text(f"Failed to load model {model_name}. Aborting Mind Meld mode.", cfg.COLOR_RED))
            return

    meld_mode = MindMeldMode(loaded_engines, args)
    meld_mode.run()


def run_game_loop(engine: LLMEngine, args: argparse.Namespace) -> None:
    """Main game loop."""
    # Get initial prompt
    ui.print_separator()
    initial_text = ui.get_user_input(
        "Enter a starting sentence (or press Enter for default)",
        allow_empty=True,
        default_val_on_empty="Mars attacks"
    )
    
    if initial_text == cfg.SHORTCUT_QUIT:
        return
    
    current_full_text = initial_text
    total_score = 0
    total_max_score = 0
    round_counter = 0
    
    # Initialize tensors for the game
    full_history_input_ids, full_history_attention_mask = engine.encode(current_full_text, add_special_tokens=True)
    incremental_input_ids_for_next_pred = full_history_input_ids
    
    # Main game loop
    while round_counter < args.steps:
        round_counter += 1
        ui.display_round_header(round_counter, args.steps)
        ui.display_current_sentence(current_full_text)
        
        # Determine input for this step
        # For proper attention and context, always use full history when KV cache is disabled
        use_kv_cache = hasattr(engine, 'engine_config') and engine.engine_config.get('use_kv_cache', cfg.PYTORCH_USE_KV_CACHE)
        
        if round_counter == 1 or not use_kv_cache:
            # First round or no KV cache: use full history
            ids_for_prediction_now = full_history_input_ids
        else:
            # Subsequent rounds with KV cache: use only new token
            ids_for_prediction_now = incremental_input_ids_for_next_pred
        
        # For KV cache, we need to handle attention mask differently
        # When using cached inference with single token, some models expect None
        if round_counter > 1 and ids_for_prediction_now is not full_history_input_ids:
            # We're using incremental generation
            attention_mask_for_prediction_now = full_history_attention_mask
        else:
            attention_mask_for_prediction_now = full_history_attention_mask
        
        # Perform prediction
        pred_result: Dict[str, Any] = engine.predict_next(
            ids_for_prediction_now,
            attention_mask_for_prediction_now,
            args.temperature,
            args.top_k,
            args.top_p,
            args.show_attention
        )
        
        # Show attention if requested
        if args.show_attention and pred_result.get("attention"):
            attn_texts, attn_scores = engine.get_attention_for_visualization(
                pred_result["attention"],
                full_history_input_ids
            )
            if attn_texts and attn_scores:
                ui.display_attention_heatmap(attn_texts, attn_scores, args.verbose)
            elif args.verbose:
                print(ui.color_text("(Attention data unavailable/unprocessed this step)", cfg.COLOR_YELLOW))
        
        # Process player guess
        score, max_s, chosen_sequence_info, correct_sequence_info = game_logic.process_player_guess(
            engine,
            pred_result,
            args,
            current_full_text,
            PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE
        )
        
        if score == -1:
            break
        
        total_score += score
        total_max_score += max_s
        
        # Determine next token based on game mode
        if args.player_choice_mode and chosen_sequence_info and score == max_s:
            next_token_id = chosen_sequence_info[0][1]
            next_token_text = chosen_sequence_info[0][0]
            print(ui.color_text(
                f"\n[Player Choice Mode] Using YOUR correct guess: '{next_token_text}'",
                cfg.COLOR_CYAN
            ))
        else:
            next_token_id = pred_result["next_token_id"]
            next_token_text = engine.get_token_text(next_token_id)
        
        # Check for end of sequence
        if hasattr(engine.tokenizer, 'eos_token_id') and next_token_id == engine.tokenizer.eos_token_id:
            print(ui.color_text("\n<End of Sequence> token generated. Ending game.", cfg.COLOR_YELLOW))
            break
        
        # Update context - decode the token and add to text
        decoded_token = engine.decode([next_token_id], skip_special_tokens=True)
        # If the decoded token is empty (e.g., special token), use the token text directly
        if not decoded_token:
            decoded_token = next_token_text
        current_full_text += decoded_token
        
        # Debug: Show what token was added
        if args.verbose:
            print(f"\n[Debug] Added token: '{next_token_text}' (ID: {next_token_id}) -> Decoded: '{decoded_token}'")
            print(f"[Debug] Full text now: '{current_full_text}'")
        
        # Update tensor tracking using engine abstraction
        import numpy as np
        next_token_array = np.array([[next_token_id]])
        next_token_tensor = engine.convert_from_numpy(next_token_array)
        
        # Ensure proper dimensions for concatenation
        full_history_input_ids = _concatenate_tensors(full_history_input_ids, next_token_tensor, dim=-1, engine=engine)
        
        # Debug output to verify accumulation
        if args.verbose and hasattr(full_history_input_ids, 'shape'):
            print(f"[Debug] Input IDs shape: {full_history_input_ids.shape}")
        
        if full_history_attention_mask is not None:
            # Create ones tensor using engine abstraction
            import numpy as np
            batch_size = 1
            if hasattr(full_history_attention_mask, 'shape'):
                if len(full_history_attention_mask.shape) > 1:
                    batch_size = full_history_attention_mask.shape[0]
            
            ones_array = np.ones((batch_size, 1))
            ones_tensor = engine.convert_from_numpy(ones_array)
            
            if ones_tensor is not None:
                full_history_attention_mask = _concatenate_tensors(
                    full_history_attention_mask,
                    ones_tensor,
                    dim=-1,
                    engine=engine
                )
        
        incremental_input_ids_for_next_pred = next_token_tensor
    
    # Game over - show final score
    ui.print_separator()
    print(f"\n🎮 {ui.color_text('GAME OVER!', cfg.COLOR_CYAN)}")
    print(f"Final Score: {total_score}/{total_max_score}")
    
    if total_max_score > 0:
        percentage = (total_score / total_max_score) * 100
        if percentage >= 80:
            print(ui.color_text("🏆 Excellent! You really understand this model!", cfg.COLOR_GREEN))
        elif percentage >= 60:
            print(ui.color_text("👍 Good job! You have a solid grasp of the model's behavior.", cfg.COLOR_YELLOW))
        elif percentage >= 40:
            print(ui.color_text("📚 Not bad! Keep practicing to improve your intuition.", cfg.COLOR_BLUE))
        else:
            print(ui.color_text("💡 Keep learning! LLMs can be unpredictable.", cfg.COLOR_MAGENTA_LIGHT))
    
    print(f"\nFinal text: \"{current_full_text}\"\n")
    
    # Offer to continue if not at EOS
    if args.allow_eos_continue and round_counter >= args.steps:
        if not (hasattr(engine.tokenizer, 'eos_token_id') and 
                pred_result.get("next_token_id") == engine.tokenizer.eos_token_id):
            continue_choice = ui.get_user_input(
                "\nMax steps reached but no <EOS>. Continue for more rounds? (y/n)",
                valid_choices=["y", "n"],
                allow_quit=False
            )
            if continue_choice.lower() == "y":
                args.steps += cfg.DEFAULT_MAX_DECODE_STEPS
                run_game_loop(engine, args)  # Recursive call to continue


def run_chat_mode(engine: LLMEngine, args: argparse.Namespace) -> None:
    """Runs a simple interactive chat session."""
    ui.print_header("Direct Chat Mode")
    print("Type 'exit' or 'quit' to end the session.")
    history = []

    while True:
        try:
            prompt = input(ui.color_text("> User: ", cfg.COLOR_YELLOW))
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.lower() in ["exit", "quit"]:
            break

        history.append({"role": "user", "content": prompt})
        
        # Use a simple text accumulation for chat history
        full_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        
        sys.stdout.write(ui.color_text("> Assistant: ", cfg.COLOR_CYAN))
        sys.stdout.flush()

        response_text = ""
        input_ids, attention_mask = engine.encode(full_prompt, add_special_tokens=True)
        
        for _ in range(args.steps): # Max tokens for response
            pred = engine.predict_next(input_ids, attention_mask, args.temperature, args.top_k, args.top_p)
            next_id = pred['next_token_id']

            if next_id == engine.get_eos_token_id():
                break

            next_token_text = engine.decode([next_id])
            response_text += next_token_text
            sys.stdout.write(next_token_text)
            sys.stdout.flush()

            # Update for next iteration
            input_ids, attention_mask = engine.encode(response_text, add_special_tokens=False)

        history.append({"role": "assistant", "content": response_text})
        print() # Newline after response

    print("\nChat session ended.")

def run_single_shot_inference(engine: LLMEngine, args: argparse.Namespace) -> None:
    """Runs a single inference and prints performance stats."""
    ui.print_header("Single-Shot Inference")
    prompt = args.prompt
    print(f"Prompt: '{prompt}'")

    start_time = time.time()
    input_ids, attention_mask = engine.encode(prompt, add_special_tokens=True)
    prompt_tokens = input_ids.shape[-1]
    response_text = ""
    completion_tokens = 0

    for _ in range(args.steps):
        pred = engine.predict_next(input_ids, attention_mask, args.temperature, args.top_k, args.top_p)
        next_id = pred['next_token_id']

        if next_id == engine.get_eos_token_id():
            break

        completion_tokens += 1
        decoded_text = engine.decode([next_id])
        response_text += decoded_text

        # Update for next iteration
        input_ids, attention_mask = engine.encode(response_text, add_special_tokens=False)

    end_time = time.time()
    wall_time = end_time - start_time

    print(f"\nResponse: {ui.color_text(response_text, cfg.COLOR_GREEN)}")
    ui.print_separator('-')
    print("Performance Statistics:")
    print(f"  Prompt Tokens:     {prompt_tokens}")
    print(f"  Completion Tokens: {completion_tokens}")
    print(f"  Total Wall Time:   {wall_time:.2f} seconds")
    if completion_tokens > 0 and wall_time > 0:
        tps = completion_tokens / wall_time
        print(f"  Tokens per Second: {tps:.2f} TPS")
    print("-" * 25)

def main():
    """Main entry point for GAMMA."""
    # Display intro
    ui.display_intro()
    
    # Parse arguments
    args = parse_arguments()
    
    # Check if user provided minimal arguments (just running 'python game.py')
    # If so, use interactive menu
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['--help', '-h']):
        if len(sys.argv) == 2:  # User asked for help
            return  # Help was already printed by argparse
        
        # No arguments provided - use interactive menu
        menu = InteractiveMenu()
        config = menu.show_main_menu()
        
        if config is None:
            print(ui.color_text("\nExiting GAMMA.", cfg.COLOR_YELLOW))
            return
        
        # Apply interactive config to args
        menu.apply_config_to_args(args, config)
    
    # Check for special modes (from either command line or interactive)
    if args.tutorial:
        run_tutorial_mode(args)
        return
    elif args.comparison:
        run_comparison_mode(args)
        return

    # Initialize engine
    engine = initialize_game_engine(args)
    if engine is None:
        print(ui.color_text("\nFailed to initialize game engine. Exiting.", cfg.COLOR_RED))
        return

    # Set random seed if specified
    if args.seed != 0:
        random.seed(args.seed)
        print(f"Random seed set to: {args.seed}")

    # Mode dispatcher
    if args.prompt:
        run_single_shot_inference(engine, args)
        return
    elif args.chat:
        run_chat_mode(engine, args)
        return
    
    # Default to game loop
    try:
        run_game_loop(engine, args)
    except KeyboardInterrupt:
        print(ui.color_text("\n\nGame interrupted by user.", cfg.COLOR_YELLOW))
    except Exception as e:
        print(ui.color_text(f"\n\nAn error occurred: {e}", cfg.COLOR_RED))
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        print(ui.color_text("\n\nThanks for playing GAMMA! 🎮", cfg.COLOR_CYAN))


if __name__ == "__main__":
    main()