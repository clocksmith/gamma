#!/usr/bin/env python3
"""
GAMMA - Game Analyzing Model Methods Attentively
Main entry point for the interactive LLM guessing game.

Now with Penteract-inspired improvements:
- Progressive difficulty levels
- Achievement system
- Session management
"""

import argparse
import sys
import time
import random
import numpy as np
from typing import Optional, List, Dict, Any

from src.core import config as cfg
from src.ui import displays as ui
from src.engines.engine_factory import get_engine, SUPPORTED_ENGINES
from src.engines.capability_registry import get_engine_info
from src.core.engine_interface import LLMEngine
from src.game.tutorial_mode import TutorialMode
from src.comparison.comparison_mode import ComparisonMode
from src.mind_meld.mode import MindMeldMode
from src.core.menu.interactive_menu import InteractiveMenu
from src.game.cli.controller import run_game_loop as controller_run_game_loop
from src.game.cli.commands import parse_arguments, apply_word_mode_presets, CLI_OVERRIDE_FLAGS



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


def _flag_was_provided(flag: str) -> bool:
    """Check whether a CLI flag (e.g., '--engine') was explicitly provided."""
    flag_variants = [flag, f"{flag}="]
    negative_flag = None
    if flag.startswith("--"):
        negative_flag = "--no-" + flag[2:]
    candidate_prefixes = list(flag_variants)
    if negative_flag:
        candidate_prefixes.extend([negative_flag, f"{negative_flag}="])
    for arg in sys.argv[1:]:
        if arg == flag:
            return True
        if negative_flag and arg == negative_flag:
            return True
        if arg.startswith(flag_variants[1]):
            return True
        if negative_flag and arg.startswith(f"{negative_flag}="):
            return True
    return False



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
        print(ui.color_text("Model loaded successfully!", cfg.COLOR_GREEN))

        # Validate engine is suitable for game mode (needs real logits/probabilities)
        # Engines that use HTTP APIs don't expose full probability distributions
        if not engine.supports_logits:
            print(ui.color_text(
                f"\nWarning: The '{args.engine}' engine cannot be used for game mode.",
                cfg.COLOR_RED
            ))
            print(ui.color_text(
                "The game requires access to full token probability distributions (logits),",
                cfg.COLOR_YELLOW
            ))
            print(ui.color_text(
                f"which are not exposed by {args.engine}'s HTTP API.",
                cfg.COLOR_YELLOW
            ))
            print("\nUse a local engine with the same model:")

            if args.engine == "ollama":
                print("   - Use 'llamacpp' engine with Ollama's GGUF file:")
                print(f"     1. Find the GGUF: ollama show {args.model} --modelfile | grep FROM")
                print("     2. Run GAMMA: gamma.py game --engine llamacpp --model /path/to/model.gguf")
            else:
                print("   - Supported engines: pytorch, pytorch_cuda, llamacpp, vllm, mlx, jax, tensorflow")
                print("   - Example: gamma.py game --engine pytorch --model google/gemma-2-2b-it")

            return None

        # Display engine configuration summary
        engine_summary = engine.get_config_summary()
        if engine_summary:
            print("\nEngine Configuration:")
            for key, value in engine_summary.items():
                print(f"  {key}: {value}")

        return engine
    except Exception as e:
        error_msg = str(e)
        print(ui.color_text(f"\nFailed to initialize engine: {error_msg}", cfg.COLOR_RED))

        # Provide helpful suggestions for common errors
        if "gated repo" in error_msg or "Access to model" in error_msg or "401 Client Error" in error_msg:
            print(ui.color_text("\nTip: This model requires authentication with Hugging Face.", cfg.COLOR_YELLOW))
            print("\nTo fix this, you can:")
            print("  1. Log in with: huggingface-cli login")
            print("  2. Or set your token: export HF_TOKEN=your_token_here")
            print("  3. Or use Ollama with local models (easiest option)")
            print("     - Install: https://ollama.ai")
            print("     - Pull a model: ollama pull gemma3:4b-it-qat")
            print("     - Select 'Ollama' engine when running GAMMA")
            print(f"\nGet your HF token at: https://huggingface.co/settings/tokens")
        elif "No module named" in error_msg:
            module_name = error_msg.split("'")[1] if "'" in error_msg else "unknown"
            print(ui.color_text(f"\nTip: Missing Python package: {module_name}", cfg.COLOR_YELLOW))
            print(f"\nTo fix this, run: pip install {module_name}")

        return None


def run_tutorial_mode(args: argparse.Namespace) -> None:
    """Run the interactive tutorial mode."""
    print(ui.color_text("\nStarting Tutorial Mode...", cfg.COLOR_CYAN))
    
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
        print(ui.color_text("\n\nThanks for learning with GAMMA!", cfg.COLOR_CYAN))


def run_comparison_mode(args: argparse.Namespace) -> None:
    """Run the model comparison mode."""
    print(ui.color_text("\nStarting Model Comparison Mode...", cfg.COLOR_CYAN))

    # Parse comparison models - accept both --comparison-models and --models
    models_to_compare = []

    # Use --models if provided, otherwise fall back to --comparison-models
    models_list = args.comparison_models_alias if args.comparison_models_alias else args.comparison_models

    if models_list:
        # Parse provided models
        for model_spec in models_list:
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
        selected_models = []
        while True:
            engine = ui.select_engine_interactively(default_engine="pytorch")
            if not engine:
                break

            model = ui.select_model_interactively(engine)
            if not model:
                continue

            selected_models.append((engine, model))

            if len(selected_models) >= 2:
                add_another = ui.get_user_input(
                    "Add another model? (y/n)",
                    valid_choices=["y", "n"],
                    allow_quit=False
                )
                if add_another.lower() == "n":
                    break
        
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
        print(ui.color_text("\n\nThanks for comparing models with GAMMA!", cfg.COLOR_CYAN))

def run_meld_mode(args: argparse.Namespace) -> None:
    """Run the Mind Meld mode."""
    print(ui.color_text("\nStarting Mind Meld Mode...", cfg.COLOR_CYAN))
    
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
        info = get_engine_info(engine_type)
        if info and not info.supports_logits:
            print(ui.color_text(
                f"\nError: The '{engine_type}' engine cannot be used for Mind Meld mode.",
                cfg.COLOR_RED
            ))
            print(ui.color_text(
                "Mind Meld requires full token probability distributions (logits),",
                cfg.COLOR_YELLOW
            ))
            print(ui.color_text(
                f"which are not exposed by {engine_type}'s HTTP API.",
                cfg.COLOR_YELLOW
            ))
            print("\nUse a local engine instead: pytorch, pytorch_cuda, llamacpp, vllm, mlx")
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
    """Main game loop with difficulty levels and session tracking."""
    controller_run_game_loop(engine, args)


def display_final_score_and_message(total_score: int, total_max_score: int, current_full_text: str) -> None:
    """Displays the final score and a message to the user."""
    ui.print_separator()
    print(f"\n{ui.color_text('GAME OVER!', cfg.COLOR_CYAN)}")
    print(f"Final Score: {total_score}/{total_max_score}")
    
    if total_max_score > 0:
        percentage = (total_score / total_max_score) * 100
        if percentage >= 80:
            print(ui.color_text("Excellent! You really understand this model!", cfg.COLOR_GREEN))
        elif percentage >= 60:
            print(ui.color_text("Good job! You have a solid grasp of the model's behavior.", cfg.COLOR_YELLOW))
        elif percentage >= 40:
            print(ui.color_text("Not bad! Keep practicing to improve your intuition.", cfg.COLOR_BLUE))
        else:
            print(ui.color_text("Keep learning! LLMs can be unpredictable.", cfg.COLOR_MAGENTA_LIGHT))
    
    print(f"\nFinal text: \"{current_full_text}\"\n")


def _format_chat_history(history: list, engine: LLMEngine) -> str:
    """Format chat history into a prompt string.

    Uses the tokenizer's chat template if available, otherwise falls back
    to a simple turn-based format.
    """
    # Try to use tokenizer's apply_chat_template if available
    if hasattr(engine.tokenizer, 'apply_chat_template'):
        try:
            return engine.tokenizer.apply_chat_template(
                history,
                tokenize=False,
                add_generation_prompt=True
            )
        except Exception:
            pass  # Fall back to simple format

    # Simple turn-based format fallback
    formatted_parts = []
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            formatted_parts.append(f"User: {content}")
        elif role == "assistant":
            formatted_parts.append(f"Assistant: {content}")
        elif role == "system":
            formatted_parts.append(f"System: {content}")

    return "\n".join(formatted_parts) + "\nAssistant:"

def _format_single_prompt(prompt: str, engine: LLMEngine, use_chat_template: bool) -> str:
    """Format a single prompt with a chat template when requested."""
    if not use_chat_template:
        return prompt
    history = [{"role": "user", "content": prompt}]
    return _format_chat_history(history, engine)


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

        # Format chat history into a prompt string
        full_prompt = _format_chat_history(history, engine)
        
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
    prompt_use_chat_template = bool(getattr(args, "prompt_chat_template", False))
    formatted_prompt = _format_single_prompt(prompt, engine, prompt_use_chat_template)
    print(f"Prompt: '{prompt}'")
    if formatted_prompt != prompt:
        print("Prompt format: chat template")
        if args.verbose:
            print("Formatted prompt:")
            print(formatted_prompt)

    start_time = time.time()
    full_input_ids, full_attention_mask = engine.encode(formatted_prompt, add_special_tokens=True)

    # Determine prompt token count
    if hasattr(full_input_ids, "shape"):
        prompt_tokens = int(full_input_ids.shape[-1])
    elif isinstance(full_input_ids, (list, tuple)):
        prompt_tokens = len(full_input_ids)
    else:
        prompt_tokens = 1

    use_kv_cache = getattr(engine, "engine_config", {}).get("use_kv_cache", cfg.PYTORCH_USE_KV_CACHE)
    incremental_input_ids = full_input_ids
    generated_token_ids: List[int] = []

    generation_start = time.time()

    for step in range(args.steps):
        # Determine inputs based on KV-cache availability
        if step == 0 or not use_kv_cache:
            ids_for_prediction = full_input_ids
        else:
            ids_for_prediction = incremental_input_ids

        attention_for_prediction = full_attention_mask if step == 0 or not use_kv_cache else full_attention_mask

        prediction = engine.predict_next(
            ids_for_prediction,
            attention_for_prediction,
            args.temperature,
            args.top_k,
            args.top_p,
            args.show_attention
        )

        next_token_id = prediction["next_token_id"]

        if args.verbose:
            token_text = engine.get_token_text(next_token_id)
            print(f"[Generation {step + 1}] token_id={next_token_id} -> '{token_text}'")

        eos_id = engine.get_eos_token_id()
        if eos_id is not None and next_token_id == eos_id:
            if args.verbose:
                print("Encountered EOS token. Stopping generation.")
            break

        generated_token_ids.append(int(next_token_id))

        # Prepare tensors for next iteration
        next_token_array = np.array([[next_token_id]])
        next_token_tensor = engine.convert_from_numpy(next_token_array)
        full_input_ids = _concatenate_tensors(full_input_ids, next_token_tensor, dim=-1, engine=engine)

        if full_attention_mask is not None:
            if hasattr(full_attention_mask, "shape"):
                batch_size = full_attention_mask.shape[0] if len(full_attention_mask.shape) > 0 else 1
            else:
                batch_size = 1
            ones_tensor = engine.convert_from_numpy(np.ones((batch_size, 1)))
            full_attention_mask = _concatenate_tensors(full_attention_mask, ones_tensor, dim=-1, engine=engine)

        incremental_input_ids = next_token_tensor if use_kv_cache else full_input_ids

    generation_end = time.time()
    completion_tokens = len(generated_token_ids)
    response_text = engine.decode(generated_token_ids, skip_special_tokens=True) if generated_token_ids else ""

    end_time = time.time()
    wall_time = end_time - start_time
    generation_time = generation_end - generation_start

    print(f"\nResponse: {ui.color_text(response_text or '[No tokens generated]', cfg.COLOR_GREEN)}")
    ui.print_separator('-')
    print("Performance Statistics:")
    print(f"  Prompt Tokens:     {prompt_tokens}")
    print(f"  Completion Tokens: {completion_tokens}")
    print(f"  Total Wall Time:   {wall_time:.2f} seconds")
    print(f"  Generation Time:   {generation_time:.2f} seconds")
    if completion_tokens > 0 and generation_time > 0:
        tps = completion_tokens / max(generation_time, 1e-8)
        print(f"  Tokens per Second: {tps:.2f} TPS")
    print("-" * 25)

def main():
    """Main entry point for GAMMA."""
    ui.display_intro()
    args = parse_arguments()

    if args.quickstart:
        print(ui.color_text("\nQuickstart mode: using quick-play defaults.", cfg.COLOR_GREEN))
        menu = InteractiveMenu()
        quick_config = menu._quick_play_classic()

        # Track CLI overrides so they persist after applying quick config
        user_overrides: Dict[str, Any] = {}
        for flag, attr in CLI_OVERRIDE_FLAGS.items():
            if _flag_was_provided(flag):
                user_overrides[attr] = getattr(args, attr)

        quick_model_spec = args.quick_model.strip() if args.quick_model else None
        if quick_model_spec:
            if ":" in quick_model_spec:
                quick_engine, quick_model_name = quick_model_spec.split(":", 1)
                quick_config['engine'] = quick_engine or quick_config.get('engine', args.engine)
                quick_config['model'] = quick_model_name
                user_overrides['engine'] = quick_config['engine']
                user_overrides['model'] = quick_model_name
            else:
                quick_config['model'] = quick_model_spec
                user_overrides.setdefault('engine', quick_config.get('engine', args.engine))
                user_overrides['model'] = quick_model_spec

        menu.apply_config_to_args(args, quick_config)

        # Re-apply explicit CLI overrides after quick config
        for attr, value in user_overrides.items():
            setattr(args, attr, value)

        apply_word_mode_presets(args)
        run_selected_mode(args)
        return

    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['--help', '-h']):
        if len(sys.argv) == 2:
            return
        
        menu = InteractiveMenu()
        config = menu.show_main_menu()
        
        if config is None:
            print(ui.color_text("\nExiting GAMMA.", cfg.COLOR_YELLOW))
            return
        
        menu.apply_config_to_args(args, config)
        apply_word_mode_presets(args)

    run_selected_mode(args)


def run_selected_mode(args: argparse.Namespace):
    """Runs the selected game mode based on parsed arguments."""
    if args.tutorial:
        run_tutorial_mode(args)
        return
    if args.comparison:
        run_comparison_mode(args)
        return
    if getattr(args, "mind_meld", False):
        run_meld_mode(args)
        return

    engine = initialize_game_engine(args)
    if engine is None:
        print(ui.color_text("\nFailed to initialize game engine. Exiting.", cfg.COLOR_RED))
        return

    if args.seed != 0:
        random.seed(args.seed)
        print(f"Random seed set to: {args.seed}")

    if args.prompt:
        run_single_shot_inference(engine, args)
    elif args.chat:
        run_chat_mode(engine, args)
    else:
        try:
            controller_run_game_loop(engine, args)
        except KeyboardInterrupt:
            print(ui.color_text("\n\nGame interrupted by user.", cfg.COLOR_YELLOW))
        except Exception as e:
            print(ui.color_text(f"\n\nAn error occurred: {e}", cfg.COLOR_RED))
            if args.verbose:
                import traceback
                traceback.print_exc()
        finally:
            print(ui.color_text("\n\nThanks for playing GAMMA!", cfg.COLOR_CYAN))


if __name__ == "__main__":
    main()
