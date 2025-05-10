import os
import sys  # For sys.stdout.isatty check

# --- Model Defaults ---
DEFAULT_ENGINE = "pytorch"
DEFAULT_MODEL_NAME = "google/gemma-2-2b-it"  # A reasonably small, good default

# Placeholders for UI prompts if specific engine models are not provided
DEFAULT_GGUF_MODEL_PLACEHOLDER = "path/to/your/model.gguf"
DEFAULT_ONNX_MODEL_PLACEHOLDER = "path/to/your/model.onnx"
DEFAULT_MLX_MODEL_PLACEHOLDER = "mlx-community/Mistral-7B-Instruct-v0.2"  # Example

# --- Sampling Defaults ---
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 8
DEFAULT_TOP_P = 0.95

# --- Game Mechanics Defaults ---
DEFAULT_MAX_DECODE_STEPS = 8
DEFAULT_NUM_CHOICES = 4
DEFAULT_PERMUTATION_LENGTH = 3  # How many tokens to guess in a sequence
DEFAULT_SHOW_ATTENTION = True
DEFAULT_VERBOSE = True  # Controls extra explanatory text during gameplay
DEFAULT_FOCUS_WORDS = False  # If true, player choices prioritize "word-like" tokens
MIN_WORD_TOKEN_LENGTH = 2  # For focus_words heuristic, min length for a token to be a word unless purely alpha

# --- UI & Visualization ---
MAX_TOKENS_FOR_PROB_DISPLAY = (
    10  # How many top tokens to show in probability breakdowns
)
USE_COLORS = True  # Global color flag, can be overridden by --no-color

# --- Engine Specific Defaults ---
# PyTorch
PYTORCH_DEVICE_MAP = "auto"
PYTORCH_ATTN_IMPLEMENTATION = "eager"  # Options: "eager", "sdpa", "flash_attention_2"
PYTORCH_USE_KV_CACHE = True  # Default to using KV cache

# Llama.cpp
LLAMA_CPP_N_GPU_LAYERS = 0  # Number of layers to offload to GPU (-1 for all)
LLAMA_CPP_N_CTX = 2048  # Context size
LLAMA_CPP_LIB_VERBOSE = False  # llama-cpp-python library's own verbose logging

# ONNX Runtime
ONNX_PROVIDERS = [
    "CPUExecutionProvider"
]  # Default to CPU. E.g., ["CUDAExecutionProvider", "CPUExecutionProvider"]
ONNX_PROVIDER_OPTIONS = None  # E.g. [{'device_id': '0'}] for CUDAExecutionProvider

# JAX/Flax
JAX_DTYPE = "float32"  # "float32", "bfloat16", "float16"

# MLX
MLX_LOAD_CONFIG = {}  # e.g. {"quant": {"group_size": 64, "bits": 4}} for 4-bit quant

# --- Terminal Colors ---
# Check if stdout is a TTY and OS to enable/disable colors
if os.name == "nt":  # Windows
    try:
        import colorama

        colorama.init()
    except ImportError:
        # Fallback for Windows without colorama if not a recognized color terminal
        if os.environ.get("TERM") not in [
            "xterm",
            "xterm-color",
            "xterm-256color",
            "linux",
            "screen",
            "vt100",
            "rxvt",
            "putty",
        ]:
            USE_COLORS = False
elif not (
    hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
):  # Not a TTY (e.g., piping output)
    USE_COLORS = False

if USE_COLORS:  # Define colors if enabled
    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_BLUE = "\033[94m"
    COLOR_YELLOW = "\033[93m"
    COLOR_CYAN = "\033[96m"
    COLOR_RESET = "\033[0m"
    COLOR_MAGENTA_DIM = "\033[38;5;54m"
    COLOR_MAGENTA_LIGHT = "\033[38;5;91m"
    COLOR_MAGENTA_MEDIUM = "\033[38;5;127m"
    COLOR_MAGENTA_BRIGHT = "\033[38;5;164m"
    COLOR_MAGENTA_INTENSE = "\033[38;5;201m"
else:  # Define empty strings if colors are disabled
    COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_CYAN = "", "", "", "", ""
    COLOR_MAGENTA_DIM, COLOR_MAGENTA_LIGHT, COLOR_MAGENTA_MEDIUM = "", "", ""
    COLOR_MAGENTA_BRIGHT, COLOR_MAGENTA_INTENSE, COLOR_RESET = "", "", ""

# --- Special Tokens Game Representations ---
TOKEN_PAD = "<pad>"
TOKEN_EOS = "<eos>"
TOKEN_BOS = "<bos>"
TOKEN_UNK = "<unk>"
TOKEN_MASK = "<mask>"
TOKEN_CLS = "<cls>"
TOKEN_SEP = "<sep>"
TOKEN_NL = "<nl>"  # Newline representation

SPECIAL_TOKEN_GAME_REPR = {
    "pad_token": TOKEN_PAD,
    "eos_token": TOKEN_EOS,
    "bos_token": TOKEN_BOS,
    "unk_token": TOKEN_UNK,
    "mask_token": TOKEN_MASK,
    "cls_token": TOKEN_CLS,
    "sep_token": TOKEN_SEP,
    # Newline token is handled by checking for specific newline_token_id attributes in engines
}

# --- Keyboard Shortcuts for UI ---
SHORTCUT_QUIT = "qqq"  # Universal quit command in prompts
SHORTCUT_CONFIRM_CONFIG_ACCEPT = "y"
SHORTCUT_CONFIRM_CONFIG_MODIFY = "m"
SHORTCUT_MODIFY_PARAM_SKIP = ""  # Pressing Enter to skip modifying a parameter
