import argparse
import sys
import time

from core import config as cfg
from core import ui
from core import game_logic
from core import explanations
from engines.engine_factory import get_engine, SUPPORTED_ENGINES
from core.engine_interface import LLMEngine

PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE = set()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GAMMA: Interactive LLM Guessing Game",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=SUPPORTED_ENGINES,
        default=None,
        help="LLM engine. Interactive if omitted.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model ID (HF name/local path). Interactive if engine set but model omitted.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=cfg.DEFAULT_MAX_DECODE_STEPS,
        help="Max game rounds.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=cfg.DEFAULT_TEMPERATURE,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--top-k", type=int, default=cfg.DEFAULT_TOP_K, help="Top-K filtering."
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=cfg.DEFAULT_TOP_P,
        help="Top-P (nucleus) filtering.",
    )
    parser.add_argument(
        "--num-choices",
        type=int,
        default=cfg.DEFAULT_NUM_CHOICES,
        help="Choices presented per round.",
    )
    parser.add_argument(
        "--permutation-length",
        type=int,
        default=cfg.DEFAULT_PERMUTATION_LENGTH,
        help="Tokens per choice sequence.",
    )
    parser.add_argument(
        "--focus-words",
        action="store_true",
        default=cfg.DEFAULT_FOCUS_WORDS,
        help="Prioritize 'word' tokens in choices.",
    )
    parser.add_argument(
        "--player-choice-mode",
        action="store_true",
        default=False,
        help="EXPERIMENTAL: Player's correct full guess drives generation.",
    )
    parser.add_argument(
        "--allow-eos-continue",
        action="store_true",
        default=False,
        help="Offer to continue generating after max_steps if EOS not hit.",
    )
    parser.add_argument(
        "--show-attention",
        action=argparse.BooleanOptionalAction,
        default=cfg.DEFAULT_SHOW_ATTENTION,
        help="Show attention visualization.",
    )
    parser.add_argument(
        "--verbose",
        action=argparse.BooleanOptionalAction,
        default=cfg.DEFAULT_VERBOSE,
        help="Enable detailed explanations.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=not cfg.USE_COLORS,
        help="Disable terminal colors.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for engines that use it (e.g., JAX, Llama.cpp).",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face Hub token for gated models.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        default=False,
        help="Trust remote code for Hugging Face models.",
    )

    pt_group = parser.add_argument_group("PyTorch Engine")
    pt_group.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="PyTorch: 4-bit quantization (bitsandbytes).",
    )
    pt_group.add_argument(
        "--bnb-4bit-quant-type",
        type=str,
        default="nf4",
        help="PyTorch 4-bit: Quant type (e.g., 'nf4', 'fp4').",
    )
    pt_group.add_argument(
        "--bnb-4bit-compute-dtype",
        type=str,
        default="bfloat16",
        help="PyTorch 4-bit: Compute dtype (e.g., 'bfloat16', 'float16').",
    )
    pt_group.add_argument(
        "--bnb-4bit-use-double-quant",
        action="store_true",
        help="PyTorch 4-bit: Use double quantization.",
    )
    pt_group.add_argument(
        "--load-in-8bit",
        action="store_true",
        help="PyTorch: 8-bit quantization (bitsandbytes).",
    )
    pt_group.add_argument(
        "--pytorch-attn",
        type=str,
        default=cfg.PYTORCH_ATTN_IMPLEMENTATION,
        choices=["eager", "sdpa", "flash_attention_2"],
        help="PyTorch: Attention implementation.",
    )
    pt_group.add_argument(
        "--pytorch-device-map",
        type=str,
        default=cfg.PYTORCH_DEVICE_MAP,
        help="PyTorch: Device map (e.g., 'auto', 'cpu', 'cuda:0').",
    )
    pt_group.add_argument(
        "--use-kv-cache",
        action=argparse.BooleanOptionalAction,
        default=cfg.PYTORCH_USE_KV_CACHE,
        help="PyTorch/TF: Use KV cache during generation.",
    )  # Generic key for PT/TF
    pt_group.add_argument(
        "--low-cpu-mem-usage",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="PyTorch: Attempt to use less CPU RAM during model loading.",
    )

    lc_group = parser.add_argument_group("Llama.cpp Engine")
    lc_group.add_argument(
        "--llama-cpp-n-gpu-layers",
        type=int,
        default=cfg.LLAMA_CPP_N_GPU_LAYERS,
        help="Llama.cpp: GPU layers (-1 for all).",
    )
    lc_group.add_argument(
        "--llama-cpp-n-ctx",
        type=int,
        default=cfg.LLAMA_CPP_N_CTX,
        help="Llama.cpp: Context size.",
    )
    lc_group.add_argument(
        "--llama-cpp-lib-verbose",
        action="store_true",
        default=cfg.LLAMA_CPP_LIB_VERBOSE,
        help="Llama.cpp: Library's internal verbose output.",
    )

    onnx_group = parser.add_argument_group("ONNX Runtime Engine")
    onnx_group.add_argument(
        "--onnx-tokenizer",
        type=str,
        default=None,
        help="ONNX: Required. HF tokenizer name/path.",
    )
    onnx_group.add_argument(
        "--onnx-providers",
        type=str,
        nargs="+",
        default=cfg.ONNX_PROVIDERS,
        help=f"ONNX: Execution providers. Default: {cfg.ONNX_PROVIDERS}",
    )

    jax_group = parser.add_argument_group("JAX Engine")
    jax_group.add_argument(
        "--jax-dtype",
        type=str,
        default=cfg.JAX_DTYPE,
        choices=["float32", "bfloat16", "float16"],
        help="JAX: Model data type.",
    )

    mlx_group = parser.add_argument_group("MLX Engine")
    mlx_group.add_argument(
        "--mlx-adapter-path", type=str, default=None, help="MLX: Path to LoRA adapter."
    )
    # mlx_load_config (quantization etc.) can be complex, added to config.py for now. Future: config file.

    parsed_args = parser.parse_args()
    if parsed_args.no_color:
        cfg.USE_COLORS = False
        for color_attr in [attr for attr in dir(cfg) if attr.startswith("COLOR_")]:
            setattr(cfg, color_attr, "")
    return parsed_args


def initialize_game_engine(args: argparse.Namespace) -> Optional[LLMEngine]:
    s_eng_name = args.engine
    s_model_id = args.model
    if not s_eng_name:
        s_eng_name = ui.select_engine_interactively(cfg.DEFAULT_ENGINE)
        if s_eng_name is None:
            return None  # User quit
        args.engine = s_eng_name  # Update args
    if not s_model_id:
        if s_eng_name == "onnx" and not args.onnx_tokenizer:
            args.onnx_tokenizer = ui.get_user_input(
                "Enter HF tokenizer for ONNX model (required)",
                allow_empty=False,
                allow_quit=True,
            )
            if args.onnx_tokenizer == cfg.SHORTCUT_QUIT:
                return None
        s_model_id = ui.select_model_interactively(
            s_eng_name,
            getattr(args, "model", None)
            or (
                cfg.DEFAULT_MODEL_NAME
                if s_eng_name not in ["llamacpp", "onnx"]
                else None
            ),
        )
        if s_model_id is None:
            return None  # User quit
        args.model = s_model_id  # Update args

    if args.engine == "onnx" and not args.onnx_tokenizer:
        print(
            ui.color_text(
                "Critical: ONNX engine needs --onnx-tokenizer to be specified for model '{args.model}'.",
                cfg.COLOR_RED,
            )
        )
        return None
    try:
        engine = get_engine(args.engine, args.model, vars(args))
        ui.display_model_loading(args.model, args.engine)
        engine.load()
        summary = engine.get_config_summary()
        if summary:
            print(ui.color_text("Engine Specifics Post-Load:", cfg.COLOR_CYAN))
            for k, v_sum in summary.items():
                print(f"  {k}: {v_sum}")
        return engine
    except Exception as e:
        ui.display_engine_error(args.engine, e)
        return None


def run_game_loop(engine: LLMEngine, args: argparse.Namespace):
    global PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE
    PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE.clear()
    ui.display_intro()
    explanations.explain_game_concepts(args)
    if args.show_attention:
        explanations.explain_attention(args)
    explanations.explain_sampling_filters(args)
    if args.focus_words:
        explanations.explain_focus_words_mode(args)
    if args.player_choice_mode:
        explanations.explain_player_choice_mode(args)

    initial_prompt = ui.get_user_input(
        f"Enter starting prompt (or Enter for default)",
        allow_empty=True,
        default_val_on_empty="The ancient scroll spoke of a power that could",
    )
    if initial_prompt == cfg.SHORTCUT_QUIT:
        return
    if initial_prompt == "The ancient scroll spoke of a power that could":
        print(f'Using default prompt: "{initial_prompt}"')

    # Initial encoding of the full prompt. Subsequent steps use incremental inputs.
    engine.reset_kv_cache()  # Ensure clean state for new prompt
    current_input_ids, current_attention_mask = engine.encode(
        initial_prompt, add_special_tokens=True
    )
    current_full_text = initial_prompt
    total_score, total_max_score = 0, 0
    game_start_time = time.time()

    for step_num in range(1, args.steps + 1):
        ui.display_round_header(step_num, args.steps)
        ui.display_current_sentence(current_full_text)

        # For the first step, input_ids is the full prompt.
        # For subsequent steps, input_ids should be just the new token(s).
        # The engine's predict_next now manages its own KV cache.
        ids_for_prediction = (
            current_input_ids
            if step_num == 1 or engine._kv_cache is None
            else current_input_ids[:, -1:]
        )
        mask_for_prediction = current_attention_mask  # Full mask for first step, or updated mask for incremental

        # If it's an incremental step, ensure attention_mask is correctly extended
        if (
            ids_for_prediction.shape[-1] == 1 and current_attention_mask is not None
        ):  # Incremental step
            # This simplistic extension works if the model expects full mask. Some models might only need mask for new token.
            # For HF models, usually the full mask is passed and internally handled with past_key_values.
            # Some engines might not need attention_mask for incremental steps if KV cache is used.
            # The engine_interface allows attention_mask to be None.
            pass  # Assuming engine handles mask with KV cache, or full mask is still passed.

        pred_result = engine.predict_next(
            ids_for_prediction,
            mask_for_prediction,
            args.temperature,
            args.top_k,
            args.top_p,
            args.show_attention,
        )

        if args.show_attention and pred_result.get("attention"):
            attn_texts, attn_scores = engine.get_attention_for_visualization(
                pred_result["attention"], current_input_ids
            )  # Pass full current_input_ids for viz context
            if attn_texts and attn_scores:
                ui.display_attention_heatmap(attn_texts, attn_scores, args.verbose)
            elif args.verbose:
                print(
                    ui.color_text(
                        "(Attention data unavailable/unprocessed this step)",
                        cfg.COLOR_YELLOW,
                    )
                )

        score, max_s, chosen_sequence_info, correct_sequence_info = (
            game_logic.process_player_guess(
                engine,
                pred_result,
                args,
                current_full_text,
                PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE,
            )
        )
        if score == -1:
            break
        total_score += score
        total_max_score += max_s

        next_tokens_info_to_append: List[Tuple[str, int]]
        if (
            args.player_choice_mode and score == max_s and chosen_sequence_info
        ):  # Perfect match in player choice mode
            next_tokens_info_to_append = chosen_sequence_info
            print(
                ui.color_text(
                    f"Perfect guess! Using your chosen sequence to continue: '{' '.join(ti[0] for ti in chosen_sequence_info)}'",
                    cfg.COLOR_GREEN,
                )
            )
        else:  # Standard mode or imperfect guess
            next_tokens_info_to_append = (
                correct_sequence_info  # This is model's top N from generate_choices
            )

        # Stop if EOS is in the chosen/correct sequence to append
        eos_token_id = next(
            (
                tid
                for tid, repr_s in engine._special_token_id_to_game_repr.items()
                if repr_s == cfg.TOKEN_EOS
            ),
            None,
        )
        hit_eos_in_append = False

        newly_appended_text_parts = []
        ids_to_actually_append_for_next_step = []

        for token_idx_in_seq, (token_text, token_id) in enumerate(
            next_tokens_info_to_append
        ):
            if args.focus_words:
                ui.display_token_explanation_if_needed(
                    engine,
                    token_id,
                    token_text,
                    PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE,
                    is_part_of_player_choice=False,
                )

            newly_appended_text_parts.append(token_text)
            ids_to_actually_append_for_next_step.append(token_id)

            if eos_token_id is not None and token_id == eos_token_id:
                hit_eos_in_append = True
                print(
                    f"\n{ui.color_text('📝 Model sequence includes End-Of-Sequence token.', cfg.COLOR_GREEN)}"
                )
                break  # Stop appending after EOS

        # Update current_full_text for display
        temp_new_text_segment = ""
        for i, part_text in enumerate(newly_appended_text_parts):
            if (
                i > 0
                and temp_new_text_segment
                and not temp_new_text_segment.endswith(" ")
                and not part_text.startswith(" ")
                and (
                    temp_new_text_segment[-1].isalnum()
                    or (part_text and part_text[0].isalnum())
                )
            ):
                temp_new_text_segment += " "
            temp_new_text_segment += part_text

        if (
            current_full_text
            and not current_full_text.endswith(" ")
            and temp_new_text_segment
            and not temp_new_text_segment.startswith(" ")
            and (current_full_text[-1].isalnum() or temp_new_text_segment[0].isalnum())
        ):
            current_full_text += " "
        current_full_text += temp_new_text_segment

        if hit_eos_in_append:
            ui.display_current_sentence(current_full_text.strip())
            break  # End game loop

        # Update input_ids and attention_mask for the next iteration
        if ids_to_actually_append_for_next_step:
            # Engine encodes only the new token(s) for incremental update
            new_ids_segment, new_mask_segment = engine.encode(
                "".join(newly_appended_text_parts).strip(), add_special_tokens=False
            )  # No BOS/EOS for incremental parts

            current_input_ids = (
                new_ids_segment  # This is what predict_next uses for its "input_ids"
            )
            # Attention mask update for incremental step is complex and engine dependent.
            # Simplification: if engine uses KV, it might not need full mask update explicitly.
            # For HF models, usually the 'predict_next' itself handles mask with past_key_values.
            # If a full mask is needed:
            if current_attention_mask is not None and new_mask_segment is not None:
                if hasattr(current_attention_mask, "shape") and hasattr(
                    new_mask_segment, "shape"
                ):  # Basic check for tensor-like
                    try:  # Attempt concatenation (engine specific tensor ops needed here)
                        if "torch" in sys.modules and isinstance(
                            current_attention_mask, sys.modules["torch"].Tensor
                        ):
                            current_attention_mask = sys.modules["torch"].cat(
                                (current_attention_mask, new_mask_segment), dim=-1
                            )
                        elif "tensorflow" in sys.modules and isinstance(
                            current_attention_mask, sys.modules["tensorflow"].Tensor
                        ):
                            current_attention_mask = sys.modules["tensorflow"].concat(
                                [current_attention_mask, new_mask_segment], axis=-1
                            )
                        elif "jax" in sys.modules and hasattr(
                            current_attention_mask, "device_buffer"
                        ):  # JAX array
                            current_attention_mask = sys.modules[
                                "jax"
                            ].numpy.concatenate(
                                (current_attention_mask, new_mask_segment), axis=-1
                            )
                        elif "numpy" in sys.modules and isinstance(
                            current_attention_mask, sys.modules["numpy"].ndarray
                        ):
                            current_attention_mask = sys.modules["numpy"].concatenate(
                                (current_attention_mask, new_mask_segment), axis=-1
                            )
                        else:
                            current_attention_mask = None  # Fallback if concat fails
                    except Exception:
                        current_attention_mask = None  # Fallback
                else:
                    current_attention_mask = None
            elif new_mask_segment is not None:  # No previous mask, use new one
                current_attention_mask = new_mask_segment
            # Else: current_attention_mask remains None or unchanged if new_mask_segment is None
        else:  # No tokens appended (e.g. error or empty sequence)
            print(
                ui.color_text(
                    "Warning: No tokens were appended for the next step. Game might stall.",
                    cfg.COLOR_YELLOW,
                )
            )
            # Potentially break or handle this state more gracefully. For now, it will re-predict on same state.

        if step_num < args.steps:
            if (
                ui.get_user_input(
                    f"Press Enter for next round (or '{cfg.SHORTCUT_QUIT}' to quit)",
                    allow_empty=True,
                )
                == cfg.SHORTCUT_QUIT
            ):
                break
        elif args.allow_eos_continue and not hit_eos_in_append:
            cont_choice = ui.get_user_input(
                "Max steps reached. Continue to EOS or quit? (y/n/q)",
                ["y", "n", "q"],
                allow_quit=False,
            ).lower()
            if cont_choice == "y":
                args.steps += cfg.DEFAULT_MAX_DECODE_STEPS
            elif cont_choice == "q":
                break
            # 'n' will just let the loop terminate naturally

    ui.display_final_score(
        total_score, total_max_score, current_full_text, time.time() - game_start_time
    )


def main():
    args = parse_arguments()
    if not ui.confirm_or_modify_config(args):
        print(ui.color_text("Config not accepted. Exiting.", cfg.COLOR_YELLOW))
        return

    engine = initialize_game_engine(args)
    if engine:
        try:
            run_game_loop(engine, args)
        except KeyboardInterrupt:
            print(ui.color_text("\nGame interrupted. Exiting.", cfg.COLOR_YELLOW))
        except Exception as e:
            print(ui.color_text(f"\nAn unexpected error occurred: {e}", cfg.COLOR_RED))
            import traceback

            traceback.print_exc()
        finally:
            print("\nGAMMA session ended.")
    else:
        print(
            ui.color_text("Failed to initialize game engine. Exiting.", cfg.COLOR_RED)
        )


if __name__ == "__main__":
    main()
