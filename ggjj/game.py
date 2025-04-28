#!/usr/bin/env python

import argparse
import sys
import time
from typing import Dict, Any, Optional, List, Tuple
import json

# Ensure the ggjj package directory is in the Python path
# This allows running the script directly from the ggjj/ directory
# Or installing it as a package.
try:
    # Try relative import first if running as part of a package
    from .core import config as cfg
    from .core import ui
    from .core import game_logic
    from .core import explanations
    from .engines import engine_factory
    from .core.engine_interface import LLMEngine
except ImportError:
    # Fallback for running script directly
    try:
        from core import config as cfg
        from core import ui
        from core import game_logic
        from core import explanations
        from engines import engine_factory
        from core.engine_interface import LLMEngine
    except ImportError as e:
         import os
         script_dir = os.path.dirname(os.path.abspath(__file__))
         parent_dir = os.path.dirname(script_dir)
         if parent_dir not in sys.path:
             sys.path.insert(0, parent_dir)
         try:
             from ggjj.core import config as cfg
             from ggjj.core import ui
             from ggjj.core import game_logic
             from ggjj.core import explanations
             from ggjj.engines import engine_factory
             from ggjj.core.engine_interface import LLMEngine
         except ImportError:
              print("ERROR: Could not import GGJJ modules.")
              print("Please ensure you are running from the correct directory or have installed the package.")
              print(f"Original error: {e}")
              sys.exit(1)


def parse_arguments() -> Tuple[Dict[str, Any], Dict[str, Any]]: # Return args and engine_config separately
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="GGJJ: The Language Model Guessing Game.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # --- Core Selection ---
    parser.add_argument(
        "-e", "--engine", type=str, default=None, # Default handled interactively
        choices=ui.SUPPORTED_ENGINES, # Use list from UI
        help="LLM engine to use. If not provided, will prompt interactively."
    )
    parser.add_argument(
        "-m", "--model", type=str, default=None,
        help="Model identifier (Hugging Face name or local path, depending on engine). Overrides interactive selection."
    )

    # --- Engine Specific Arguments ---
    # Group engine args for better help message organization
    engine_group = parser.add_argument_group('Engine-Specific Options')

    # PyTorch specific
    engine_group.add_argument("--load-in-4bit", action="store_true", help="[PyTorch] Load model with 4-bit quantization.")
    engine_group.add_argument("--load-in-8bit", action="store_true", help="[PyTorch] Load model with 8-bit quantization.")
    engine_group.add_argument("--pytorch-attn", type=str, default=cfg.PYTORCH_ATTN_IMPLEMENTATION,
                        choices=['eager', 'sdpa', 'flash_attention_2'],
                        help="[PyTorch] Attention implementation to use.")

    # Llama.cpp specific
    engine_group.add_argument("--llama-cpp-n-gpu-layers", type=int, default=None, # Use None to distinguish from explicit 0
                        help=f"[Llama.cpp] Number of layers to offload to GPU (-1 for all). Default: {cfg.LLAMA_CPP_N_GPU_LAYERS}")
    engine_group.add_argument("--llama-cpp-n-ctx", type=int, default=None,
                        help=f"[Llama.cpp] Context window size. Default: {cfg.LLAMA_CPP_N_CTX}")

    # ONNX specific
    engine_group.add_argument("--onnx-providers", type=str, default=None, # Default handled by config
                         help=f"[ONNX] Comma-separated list of execution providers (e.g., 'CUDAExecutionProvider,CPUExecutionProvider'). Default: {','.join(cfg.ONNX_PROVIDERS)}")
    engine_group.add_argument("--onnx-tokenizer", type=str, default=None,
                         help="[ONNX] Required: Hugging Face name or path for the tokenizer associated with the ONNX model.")
    # Example for provider options (more complex parsing might be needed)
    # engine_group.add_argument("--onnx-provider-options", type=str, default=None,
    #                      help="[ONNX] JSON string for provider options (e.g., '[{\"device_id\":\"0\"}]')")

    # JAX specific
    engine_group.add_argument("--jax-dtype", type=str, default=cfg.JAX_DTYPE, choices=['float32', 'bfloat16', 'float16'],
                         help="[JAX] Data type for model loading.")

    # MLX specific (No specific args added yet, maybe load config path?)


    # --- Sampling Parameters ---
    sampling_group = parser.add_argument_group('Sampling Parameters')
    sampling_group.add_argument(
        "-t", "--temperature", type=float, default=cfg.DEFAULT_TEMPERATURE,
        help="Sampling temperature."
    )
    sampling_group.add_argument(
        "--top-k", type=int, default=cfg.DEFAULT_TOP_K,
        help="Top-K filtering."
    )
    sampling_group.add_argument(
        "--top-p", type=float, default=cfg.DEFAULT_TOP_P,
        help="Top-P (nucleus) filtering."
    )

    # --- Game Mechanics ---
    game_group = parser.add_argument_group('Game Mechanics')
    game_group.add_argument(
        "--steps", type=int, default=cfg.DEFAULT_MAX_DECODE_STEPS, dest="max_decode_steps",
        help="Maximum number of prediction rounds."
    )
    game_group.add_argument(
        "--choices", type=int, default=cfg.DEFAULT_NUM_CHOICES, dest="num_choices",
        help="Number of choices presented per round."
    )
    game_group.add_argument(
        "--choice-len", type=int, default=cfg.DEFAULT_PERMUTATION_LENGTH, dest="permutation_length",
        help="Number of tokens in each choice sequence."
    )

    # --- Display/UI ---
    display_group = parser.add_argument_group('Display Options')
    display_group.add_argument(
        "--no-attention", action="store_false", dest="show_attention", default=cfg.DEFAULT_SHOW_ATTENTION,
        help="Disable attention heatmap visualization (may not be supported by all engines)."
    )
    display_group.add_argument(
        "--minimal", action="store_false", dest="verbose", default=cfg.DEFAULT_VERBOSE,
        help="Run in minimal mode (less explanation text)."
    )
    display_group.add_argument(
        "--no-color", action="store_false", dest="use_color", default=cfg.USE_COLORS,
        help="Disable colored terminal output."
    )

    # --- Explanations ---
    explain_group = parser.add_argument_group('Explanation Options')
    explain_group.add_argument(
        "--explain-concepts", action="store_true", help="Explain core game concepts before starting."
    )
    explain_group.add_argument(
        "--explain-attention", action="store_true", help="Explain attention mechanism before starting."
    )
    explain_group.add_argument(
        "--explain-sampling", action="store_true", help="Explain sampling before starting."
    )

    args = parser.parse_args()
    args_dict = vars(args)

    # --- Post-process/validate arguments ---
    if args.load_in_4bit and args.load_in_8bit:
         parser.error("Cannot use both --load-in-4bit and --load-in-8bit simultaneously.")

    # Apply color setting globally
    if not args.use_color:
        cfg.USE_COLORS = False
        cfg.COLOR_RED = "" # Reset constants if needed globally
        cfg.COLOR_GREEN = ""
        cfg.COLOR_BLUE = ""
        cfg.COLOR_YELLOW = ""
        cfg.COLOR_MAGENTA_DIM = ""
        cfg.COLOR_MAGENTA_LIGHT = ""
        cfg.COLOR_MAGENTA_MEDIUM = ""
        cfg.COLOR_MAGENTA_BRIGHT = ""
        cfg.COLOR_MAGENTA_INTENSE = ""
        cfg.COLOR_RESET = ""

    # Clamp core game values
    args_dict['temperature'] = max(0.01, args.temperature)
    args_dict['top_k'] = max(0, args.top_k)
    args_dict['top_p'] = min(1.0, max(0.0, args.top_p))
    args_dict['max_decode_steps'] = max(1, args.max_decode_steps)
    args_dict['num_choices'] = max(2, args.num_choices)
    args_dict['permutation_length'] = max(1, args.permutation_length)


    # --- Construct Engine Config ---
    # Start with empty and populate based on args or defaults only if needed by the engine
    engine_config = {}

    # PyTorch
    engine_config["load_in_4bit"] = args.load_in_4bit
    engine_config["load_in_8bit"] = args.load_in_8bit
    engine_config["attn_implementation"] = args.pytorch_attn

    # Llama.cpp (Use arg value if provided, otherwise use config default)
    engine_config["n_gpu_layers"] = args.llama_cpp_n_gpu_layers if args.llama_cpp_n_gpu_layers is not None else cfg.LLAMA_CPP_N_GPU_LAYERS
    engine_config["n_ctx"] = args.llama_cpp_n_ctx if args.llama_cpp_n_ctx is not None else cfg.LLAMA_CPP_N_CTX
    engine_config["verbose"] = args.verbose # Pass game verbosity

    # ONNX
    engine_config["providers"] = args.onnx_providers.split(',') if args.onnx_providers else cfg.ONNX_PROVIDERS
    engine_config["tokenizer_name_or_path"] = args.onnx_tokenizer
    # Add provider options parsing here if needed

    # JAX
    engine_config["dtype"] = args.jax_dtype

    # MLX
    engine_config["load_config"] = cfg.MLX_LOAD_CONFIG # Use default for now

    # General
    engine_config["trust_remote_code"] = False # Could add an arg for this if needed


    # --- Handle Interactive Selection ---
    # If engine or model not specified, use interactive UI
    # Check if args_dict has values set by argparse (even if default=None)
    engine_arg_provided = args.engine is not None
    model_arg_provided = args.model is not None

    if not engine_arg_provided or not model_arg_provided:
        print("\nEngine or model not specified via command-line arguments.")
        print("Starting interactive selection...")
        selected_engine, selected_model = ui.select_engine_and_model()
        if selected_engine is None: # User quit
              print("Exiting.")
              sys.exit(0)
        # Update args_dict only if the args were not provided initially
        if not engine_arg_provided:
             args_dict['engine'] = selected_engine
        if not model_arg_provided:
             args_dict['model'] = selected_model
        # Re-read engine name after potential interactive selection
        current_engine_name = args_dict['engine']
    else:
        current_engine_name = args.engine # Use the engine provided via args

    # --- Final Validation based on final engine choice ---
    if current_engine_name == 'onnx' and not args_dict.get('onnx_tokenizer'):
         # Try getting from engine_config (might have been set via other means)
         if not engine_config.get('tokenizer_name_or_path'):
              parser.error("Argument --onnx-tokenizer is required when using the 'onnx' engine.")
         else:
              # Ensure args_dict used for display later is updated
              args_dict['onnx_tokenizer'] = engine_config['tokenizer_name_or_path']


    return args_dict, engine_config


def run_game(args: Dict[str, Any], engine_config: Dict[str, Any]):
    """Main function to run the GGJJ game."""

    # --- Initial Setup ---
    ui.display_intro()
    # Display config *after* potentially selecting engine/model interactively
    ui.display_config(args)

    # --- Explanations (Optional) ---
    if args.get("explain_concepts"): explanations.explain_game_concepts(args['verbose'])
    if args.get("explain_attention"): explanations.explain_attention(args['verbose'])
    if args.get("explain_sampling"): explanations.explain_sampling(args['temperature'], args['top_k'], args['top_p'], args['verbose'])


    # --- Load Engine and Model ---
    engine: Optional[LLMEngine] = None
    engine_name = args['engine']
    model_identifier = args['model']
    try:
        # Pass the fully constructed engine_config
        engine = engine_factory.get_engine(engine_name, model_identifier, engine_config)
        ui.display_model_loading(model_identifier)
        engine.load()
    except (ImportError, RuntimeError, ValueError, Exception) as e:
        ui.display_engine_error(engine_name, e)
        ui.display_loading_error(model_identifier, e)
        # Print specific hints
        if "tokenizer_name_or_path" in str(e) and engine_name == 'onnx':
             print(ui.color_text("Hint: Use the --onnx-tokenizer argument to specify the required tokenizer path/name.", cfg.COLOR_YELLOW))
        if "Apple Silicon Mac" in str(e):
             print(ui.color_text("Hint: The 'mlx' engine only works on Macs with M1/M2/M3 or later chips.", cfg.COLOR_YELLOW))
        sys.exit(1)

    # --- Get Starting Input ---
    start_prompt = f"\nEnter a sentence to start (or press Enter for a default, '{cfg.SHORTCUT_QUIT}' to quit)"
    input_text = ui.get_user_input(start_prompt, None, allow_quit=True)

    if input_text == cfg.SHORTCUT_QUIT: print("Exiting."); return
    elif not input_text: input_text = "The journey began"; print(f"Using default start: \"{input_text}\"")

    # --- Initialize Game State ---
    try:
        current_input_ids, current_attention_mask = engine.encode(input_text)
        # Get initial token list for display/tracking
        if isinstance(current_input_ids, list):
             full_token_ids = current_input_ids[:] # Copy list
        elif hasattr(current_input_ids, 'tolist'): # Covers numpy, torch, tf, jax, mlx
             id_list = current_input_ids.tolist()
             if isinstance(id_list[0], list): id_list = id_list[0] # Handle nested list from batch dim
             full_token_ids = id_list
        else:
             print("Warning: Could not convert initial input_ids to list for tracking.")
             full_token_ids = []

    except Exception as e:
         print(ui.color_text(f"Error encoding initial text: {e}", cfg.COLOR_RED))
         sys.exit(1)

    total_score = 0
    total_max_score = 0
    attention_history = []

    # --- Main Game Loop ---
    for step in range(args['max_decode_steps']):
        ui.display_round_header(step + 1)

        try:
            current_sentence_text = engine.decode(full_token_ids, skip_special_tokens=True)
        except Exception as e:
            print(ui.color_text(f"Error decoding sequence: {e}", cfg.COLOR_YELLOW))
            current_sentence_text = "[Decoding Error]"

        ui.display_current_sentence(current_sentence_text)

        # 1. Get Model Prediction
        try:
            prediction_result = engine.predict_next(
                input_ids=current_input_ids,
                attention_mask=current_attention_mask,
                temperature=args['temperature'],
                top_k=args['top_k'],
                top_p=args['top_p'],
                output_attentions=args['show_attention'],
                # output_hidden_states=False # Not currently used
            )
            if args['verbose']:
                 print(f"  (Model inference time: {prediction_result['forward_time']:.3f}s)")

        except Exception as e:
            print(ui.color_text(f"\n❌ Error during model prediction in round {step + 1}: {e}", cfg.COLOR_RED))
            import traceback
            traceback.print_exc()
            print(ui.color_text("   Skipping this round.", cfg.COLOR_RED))
            time.sleep(2)
            continue # Skip to next round if prediction fails

        # 2. Display Attention (if enabled and available)
        if args['show_attention'] and prediction_result.get('attention') is not None:
            viz_data = engine.get_attention_for_visualization(
                prediction_result['attention'], current_input_ids
            )
            if viz_data:
                 tokens, scores = viz_data
                 ui.display_attention_heatmap(tokens, scores, args['verbose'])
                 attention_history.append((tokens, scores))
            # Engine impl handles message if not supported

        # 3. Process Player Guess
        try:
            guess_result = game_logic.process_player_guess(
                engine=engine,
                prediction_result=prediction_result,
                num_choices=args['num_choices'],
                permutation_length=args['permutation_length'],
                current_sentence=current_sentence_text,
                verbose=args['verbose']
            )
            step_score, step_max_score, _, _ = guess_result
            if step_score == -1: print("Exiting game."); return # User quit
            total_score += step_score
            total_max_score += step_max_score
        except Exception as e:
            print(ui.color_text(f"\n❌ Error processing guess/probabilities: {e}", cfg.COLOR_RED))
            import traceback
            traceback.print_exc()
            print(ui.color_text("   Skipping probability display for this round.", cfg.COLOR_RED))
            # Can we still proceed? Need the next token ID from prediction_result
            next_token_id = prediction_result.get('next_token_id')
            if next_token_id is None:
                 print(ui.color_text("   Cannot determine next token. Ending game.", cfg.COLOR_RED))
                 break # End game if we can't get next token
            # If we have next token, skip score update and proceed? Or end round? Let's proceed carefully.
            time.sleep(2)
            # Fall through to update sequence, but score won't be updated


        # 4. Update Sequence with Model's Choice
        next_token_id = prediction_result['next_token_id'] # Should be standard int
        next_token_text = engine.get_token_text(next_token_id)
        special_repr = engine.get_special_token_representation(next_token_id)
        print("\n--- Model Appends Token ---")
        ui.display_token_info(next_token_id, next_token_text, bool(special_repr))

        full_token_ids.append(next_token_id)

        if special_repr == cfg.TOKEN_EOS:
            print(ui.color_text("\n🏁 Model generated End-of-Sequence token. Game finished.", cfg.COLOR_GREEN))
            break

        # Update engine inputs for the next iteration by re-encoding
        try:
            # Decode the full sequence including the new token
            updated_text = engine.decode(full_token_ids, skip_special_tokens=False)
            current_input_ids, current_attention_mask = engine.encode(updated_text)
        except Exception as e:
             print(ui.color_text(f"Error re-encoding sequence for next step: {e}", cfg.COLOR_RED))
             print(ui.color_text("Cannot continue.", cfg.COLOR_RED))
             break


        # Optional pause between rounds
        if step < args['max_decode_steps'] - 1:
            input("\nPress Enter for the next round...")
        else:
             print("\nMaximum rounds reached.")


    # --- Game End ---
    try:
         final_text = engine.decode(full_token_ids, skip_special_tokens=True)
    except Exception as e:
         print(ui.color_text(f"Error decoding final text: {e}", cfg.COLOR_YELLOW))
         final_text = "[Decoding Error]"
    ui.display_final_score(total_score, total_max_score, final_text)


if __name__ == "__main__":
    try:
        parsed_args, engine_cfg = parse_arguments()
        run_game(parsed_args, engine_cfg)
    except KeyboardInterrupt:
        print("\nGame interrupted by user. Exiting.")
        sys.exit(0)
    except Exception as main_error:
        print(ui.color_text(f"\n\n--- UNEXPECTED ERROR ---", cfg.COLOR_RED))
        print(ui.color_text(f"An error occurred: {main_error}", cfg.COLOR_RED))
        import traceback
        print(ui.color_text("Traceback:", cfg.COLOR_RED))
        traceback.print_exc()
        print(ui.color_text("------------------------", cfg.COLOR_RED))
        sys.exit(1)