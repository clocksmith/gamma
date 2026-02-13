"""
GAMMA CLI Command Definitions

This module contains all argument parsing and CLI configuration.
"""

import argparse
from typing import Dict, Any

from src.core import config as cfg
from src.engines.engine_factory import SUPPORTED_ENGINES


CLI_OVERRIDE_FLAGS: Dict[str, str] = {
    "--engine": "engine",
    "--model": "model",
    "--steps": "steps",
    "--temperature": "temperature",
    "--top-k": "top_k",
    "--top-p": "top_p",
    "--sampling-strategy": "sampling_strategy",
    "--num-choices": "num_choices",
    "--permutation-length": "permutation_length",
    "--focus-words": "focus_words",
    "--player-choice-mode": "player_choice_mode",
    "--show-attention": "show_attention",
    "--verbose": "verbose",
    "--show-token-details": "show_token_details",
    "--word-mode": "word_mode",
    "--prompt": "prompt",
    "--prompt-chat-template": "prompt_chat_template",
    "--prompt-system": "prompt_system",
    "--no-default-system": "no_default_system",
    "--no-step-delay": "no_step_delay",
    "--summary-only": "summary_only",
    "--order-neutral": "order_neutral",
    "--repetition-penalty": "repetition_penalty",
    "--llama-cpp-auto-gpu": "llama_cpp_auto_gpu",
}


def apply_word_mode_presets(args: argparse.Namespace) -> None:
    """Apply convenience adjustments when word-mode is enabled."""
    if not getattr(args, "word_mode", False):
        return
    # If user kept default permutation length, expand to cover typical word-piece span
    if getattr(args, "permutation_length", cfg.DEFAULT_PERMUTATION_LENGTH) == cfg.DEFAULT_PERMUTATION_LENGTH:
        args.permutation_length = 4
    args.focus_words = True


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GAMMA: Interactive LLM Guessing Game - Test your intuition against language models!\n\nRun without arguments for interactive configuration.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=True
    )

    # Core arguments
    parser.add_argument(
        "--engine",
        type=str,
        choices=SUPPORTED_ENGINES,
        default="pytorch",
        help=(
            "LLM engine: llamacpp (GGUF files), pytorch (HuggingFace), "
            "tensorflow/jax/onnx/mlx (experimental). Wrapper engines "
            "(openai, huggingface_inference, ollama) do not expose logits."
        ),
    )
    parser.add_argument("--model", type=str, default=None,
                        help="Model ID (HF name/local path). Interactive selection if omitted.")
    parser.add_argument("--quickstart", action="store_true", default=False,
                        help="Skip the interactive menu and launch using quick-play defaults.")
    parser.add_argument("--quick-model", type=str, default=None,
                        help="Override the quickstart model (accepts ENGINE:MODEL or a model name).")

    # Game parameters
    parser.add_argument("--steps", type=int, default=cfg.DEFAULT_MAX_DECODE_STEPS,
                        help="Maximum game rounds")
    parser.add_argument("--temperature", type=float, default=cfg.DEFAULT_TEMPERATURE,
                        help="Sampling temperature (lower = more focused)")
    parser.add_argument("--top-k", type=int, default=cfg.DEFAULT_TOP_K,
                        help="Top-K filtering (limits vocabulary)")
    parser.add_argument("--top-p", type=float, default=cfg.DEFAULT_TOP_P,
                        help="Top-P (nucleus) filtering")
    parser.add_argument("--sampling-strategy", type=str, default=None,
                        choices=["sample", "argmax", "greedy", "stochastic"],
                        help="Sampling strategy: sample (stochastic) or argmax (greedy). Defaults to sample for interactive, argmax for benchmark")
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
    parser.add_argument("--models", type=str, nargs="+", default=None, dest="comparison_models_alias",
                        help="Alias for --comparison-models (for consistency with other commands)")
    parser.add_argument("--chat", action="store_true", default=False,
                        help="Enable simple, direct chat mode.")
    parser.add_argument("--prompt", type=str, default=None,
                        help="Run single-shot inference with the given prompt.")
    parser.add_argument("--prompt-chat-template", action=argparse.BooleanOptionalAction, default=None,
                        help="Format --prompt using the tokenizer's chat template (auto when available).")
    parser.add_argument("--prompt-system", type=str, default=None,
                        help="System prompt to apply when using chat templates.")
    parser.add_argument("--no-default-system", action="store_true", default=False,
                        help="Disable the default system prompt for chat templates.")
    parser.add_argument("--show-token-details", action="store_true", default=False,
                        help="Display token IDs, raw pieces, and decoded previews for each choice.")
    parser.add_argument("--word-mode", action="store_true", default=False,
                        help="Convenience toggle that favors word-level play (enables focus words and expands token sequences).")

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
    _add_pytorch_args(parser)

    # Llama.cpp Engine options
    _add_llamacpp_args(parser)

    # ONNX Runtime options
    _add_onnx_args(parser)

    # JAX options
    _add_jax_args(parser)

    # Mind Meld options
    _add_mind_meld_args(parser)

    # MLX options
    _add_mlx_args(parser)

    parsed_args = parser.parse_args()

    # Handle color settings
    if parsed_args.no_color:
        cfg.USE_COLORS = False
        for color_attr in [attr for attr in dir(cfg) if attr.startswith("COLOR_")]:
            setattr(cfg, color_attr, "")

    # Apply word-mode presets if requested
    apply_word_mode_presets(parsed_args)

    return parsed_args


def _add_pytorch_args(parser: argparse.ArgumentParser) -> None:
    """Add PyTorch-specific arguments."""
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


def _add_llamacpp_args(parser: argparse.ArgumentParser) -> None:
    """Add Llama.cpp-specific arguments."""
    lc_group = parser.add_argument_group("Llama.cpp Engine Options")
    lc_group.add_argument(
        "--llama-cpp-auto-gpu",
        action=argparse.BooleanOptionalAction,
        default=cfg.LLAMA_CPP_AUTO_GPU,
        help="Llama.cpp: Auto-enable full GPU offload (-1 layers) when GPU backend is available",
    )
    lc_group.add_argument("--llama-cpp-n-gpu-layers", type=int, default=cfg.LLAMA_CPP_N_GPU_LAYERS,
                          help="Llama.cpp: GPU layers (-1 for all)")
    lc_group.add_argument("--llama-cpp-n-ctx", type=int, default=cfg.LLAMA_CPP_N_CTX,
                          help="Llama.cpp: Context size")
    lc_group.add_argument("--llama-cpp-lib-verbose", action="store_true",
                          default=cfg.LLAMA_CPP_LIB_VERBOSE,
                          help="Llama.cpp: Library's internal verbose output")


def _add_onnx_args(parser: argparse.ArgumentParser) -> None:
    """Add ONNX-specific arguments."""
    onnx_group = parser.add_argument_group("ONNX Runtime Engine Options")
    onnx_group.add_argument("--onnx-tokenizer", type=str, default=None,
                            help="ONNX: Required. HF tokenizer name/path")
    onnx_group.add_argument("--onnx-providers", type=str, nargs="+",
                            default=cfg.ONNX_PROVIDERS,
                            help="ONNX: Execution providers")


def _add_jax_args(parser: argparse.ArgumentParser) -> None:
    """Add JAX-specific arguments."""
    jax_group = parser.add_argument_group("JAX Engine Options")
    jax_group.add_argument("--jax-dtype", type=str, default=cfg.JAX_DTYPE,
                           choices=["float32", "bfloat16", "float16"],
                           help="JAX: Model data type")


def _add_mind_meld_args(parser: argparse.ArgumentParser) -> None:
    """Add Mind Meld-specific arguments."""
    mind_group = parser.add_argument_group("Mind Meld Options")
    mind_group.add_argument("--mind-meld", action="store_true", default=False,
                            help="Run Mind Meld mode to meld multiple models during generation")
    mind_group.add_argument("--meld-models", type=str, nargs="+", default=None,
                            help="Models to use for Mind Meld (format: engine:model or model to default to PyTorch)")
    mind_group.add_argument("--swap-strategy", type=str, default="pattern",
                            choices=["pattern", "fixed", "fixed_interval", "round_robin", "random",
                                     "confidence", "perplexity", "attention", "weighted", "semantic"],
                            help="Strategy for deciding when to swap active models")
    mind_group.add_argument("--fixed-interval", type=int, default=8,
                            help="Token interval for the fixed swap strategy")
    mind_group.add_argument("--use-blending", action="store_true", default=False,
                            help="Blend logits from all models instead of hard swapping")
    mind_group.add_argument("--use-weighted-average", action="store_true", default=False,
                            help="Use weighted averaging of model probabilities each step")
    mind_group.add_argument("--order-neutral", action="store_true", default=False,
                            help="Alias for --use-weighted-average to reduce swap-order sensitivity")
    mind_group.add_argument("--soft-swap", action="store_true", default=False,
                            help="Blend all models each step but keep swap cadence by boosting the active model")
    mind_group.add_argument("--soft-swap-weight", type=float, default=1.5,
                            help="Weight multiplier for the active model when --soft-swap is enabled")
    mind_group.add_argument("--use-abe", action="store_true", default=False,
                            help="Enable Agreement-Based Ensembling (ABE)")
    mind_group.add_argument("--use-speculative", action="store_true", default=False,
                            help="Enable speculative decoding (draft model proposes, target verifies)")
    mind_group.add_argument("--speculative-k", type=int, default=4,
                            help="Speculative decoding lookahead length (k)")
    mind_group.add_argument("--use-contrastive", action="store_true", default=False,
                            help="Enable contrastive decoding (expert vs amateur models)")
    mind_group.add_argument("--use-moe-router", action="store_true", default=False,
                            help="Enable content-aware MoE routing between models")
    mind_group.add_argument("--use-feedback-loop", action="store_true", default=False,
                            help="Enable feedback loop refinement (generator/critic)")
    mind_group.add_argument("--use-adversarial", action="store_true", default=False,
                            help="Enable adversarial debate mode (red team vs blue team)")
    mind_group.add_argument("--use-hierarchical", action="store_true", default=False,
                            help="Enable hierarchical control (planner/executor)")
    mind_group.add_argument("--use-sparse-ot", action="store_true", default=False,
                            help="Enable sparse OT projection for cross-tokenizer blending")
    mind_group.add_argument("--skip-compatibility-check", action="store_true", default=False,
                            help="Skip model compatibility validation (faster startup)")
    mind_group.add_argument("--use-enhanced", action="store_true", default=False,
                            help="Enable enhanced Mind Meld features (enables --translate-logits, --meld-diagnostics, --use-stats-tracker)")
    mind_group.add_argument("--blend-strategy", type=str, default="weighted_average",
                            choices=[
                                "weighted_average",
                                "confidence_weighted",
                                "dynamic_weighted",
                                "attention_weighted",
                                "learned",
                                "hierarchical",
                                "ensemble_voting"
                            ],
                            help="Logit blending strategy when blending is enabled")
    mind_group.add_argument("--alignment-strategy", type=str, default="intersection",
                            help="Vocabulary alignment strategy: intersection, align, subword, semantic_map, unk, auto")
    mind_group.add_argument("--translate-logits", action="store_true", default=False,
                            help="Translate active model logits into the next model's vocabulary during swaps (experimental)")
    mind_group.add_argument("--max-sentences", type=int, default=None,
                            help="Stop Mind Meld after N sentences in generated output")
    mind_group.add_argument("--stop-text", action="append", default=[],
                            help="Stop Mind Meld when generated output contains this text (repeatable)")
    mind_group.add_argument("--repetition-penalty", type=float, default=None,
                            help="Repetition penalty (>1.0 reduces repeats) for sampling")
    mind_group.add_argument("--use-stats-tracker", action="store_true", default=False,
                            help="Track Mind Meld statistics and optionally write them to a file")
    mind_group.add_argument("--stats-file", type=str, default=None,
                            help="Path to save Mind Meld statistics (requires --use-stats-tracker)")
    mind_group.add_argument("--initial-prompt", type=str, default=None,
                            help="Initial prompt to seed Mind Meld generation")
    mind_group.add_argument("--shared-chat-template", action=argparse.BooleanOptionalAction, default=None,
                            help="Mind Meld only: use a single chat template across models (reduces order sensitivity)")
    mind_group.add_argument("--use-model-offloading", action="store_true", default=False,
                            help="Offload inactive models to CPU to save GPU memory (useful for large models)")
    mind_group.add_argument("--headless", action="store_true", default=False,
                            help="Run Mind Meld without interactive prompts or visual output")
    mind_group.add_argument("--meld-diagnostics", action="store_true", default=False,
                            help="Log Mind Meld diagnostics (KV cache bridging and vocab translation)")
    mind_group.add_argument("--allow-kv-cache-translation", action="store_true", default=False,
                            help="Allow KV cache translation across mismatched models (experimental)")
    mind_group.add_argument("--force-kv-cache-translation", action="store_true", default=False,
                            help="Force KV cache translation even when safety checks fail (unsafe)")
    mind_group.add_argument("--no-step-delay", action="store_true", default=False,
                            help="Mind Meld only: disable the 1-second delay between steps")
    mind_group.add_argument("--summary-only", action="store_true", default=False,
                            help="Mind Meld only: show only the final output and brief stats")


def _add_mlx_args(parser: argparse.ArgumentParser) -> None:
    """Add MLX-specific arguments."""
    mlx_group = parser.add_argument_group("MLX Engine Options")
    mlx_group.add_argument("--mlx-adapter-path", type=str, default=None,
                           help="MLX: Path to LoRA adapter")
