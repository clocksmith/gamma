# ggjj/core/config.py

import os

# --- Model Defaults ---
DEFAULT_ENGINE = "pytorch"
# DEFAULT_MODEL_NAME = "google/gemma-2-2b-it" # No longer needed as primary default; handled interactively based on engine
DEFAULT_GGUF_MODEL_PLACEHOLDER = "path/to/your/model.gguf" # Example for UI prompts
DEFAULT_ONNX_MODEL_PLACEHOLDER = "path/to/your/model.onnx" # Example for UI prompts

# --- Sampling Defaults ---
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 8
DEFAULT_TOP_P = 0.95

# --- Game Mechanics Defaults ---
DEFAULT_MAX_DECODE_STEPS = 8
DEFAULT_NUM_CHOICES = 4 # Number of options presented to the player
DEFAULT_PERMUTATION_LENGTH = 3 # Number of tokens shown in each choice guess
DEFAULT_SHOW_ATTENTION = True
DEFAULT_VERBOSE = True # Default to showing detailed explanations

# --- UI & Visualization ---
MAX_TOKENS_FOR_PROB_DISPLAY = 10 # Max tokens in probability lists
USE_COLORS = True # Attempt to use colors by default

# --- Engine Specific Defaults (can be overridden by args/config) ---
# PyTorch specific settings
PYTORCH_DEVICE_MAP = "auto"
PYTORCH_ATTN_IMPLEMENTATION = "eager"

# Llama.cpp specific settings (Example Defaults)
LLAMA_CPP_N_GPU_LAYERS = 0 # Default to CPU
LLAMA_CPP_N_CTX = 2048    # Default context size

# ONNX Runtime specific settings (Example Defaults)
ONNX_PROVIDERS = ["CPUExecutionProvider"] # Default to CPU
ONNX_PROVIDER_OPTIONS = None

# JAX specific settings (Example Defaults)
JAX_DTYPE = "float32"

# MLX specific settings (Example Defaults)
MLX_LOAD_CONFIG = {}

# --- Available Models (REMOVED) ---
# This is no longer used as model identifier depends on the chosen engine.
# AVAILABLE_MODELS = { ... }

# --- Terminal Colors ---
# Basic check for color support
if os.name == "nt": # Windows check
    try:
        import colorama
        colorama.init()
    except ImportError:
        # Basic check if TERM environment variable suggests color support
        if os.environ.get("TERM") not in ["xterm", "xterm-color", "xterm-256color", "linux", "screen"]:
            USE_COLORS = False
elif not os.isatty(1): # Check if stdout is a tty
    USE_COLORS = False

# Define colors only if enabled
if USE_COLORS:
    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_BLUE = "\033[94m"
    COLOR_YELLOW = "\033[93m"
    COLOR_MAGENTA_DIM = "\033[38;5;54m"   # Very light magenta
    COLOR_MAGENTA_LIGHT = "\033[38;5;91m"  # Light magenta
    COLOR_MAGENTA_MEDIUM = "\033[38;5;127m" # Medium magenta
    COLOR_MAGENTA_BRIGHT = "\033[38;5;164m" # Bright magenta
    COLOR_MAGENTA_INTENSE = "\033[38;5;201m" # Intense magenta
    COLOR_RESET = "\033[0m"
else:
    COLOR_RED = ""
    COLOR_GREEN = ""
    COLOR_BLUE = ""
    COLOR_YELLOW = ""
    COLOR_MAGENTA_DIM = ""
    COLOR_MAGENTA_LIGHT = ""
    COLOR_MAGENTA_MEDIUM = ""
    COLOR_MAGENTA_BRIGHT = ""
    COLOR_MAGENTA_INTENSE = ""
    COLOR_RESET = ""

# --- Special Tokens ---
# Define constants for special token representations used in the game UI
TOKEN_PAD = "<pad>"
TOKEN_EOS = "<eos>"
TOKEN_BOS = "<bos>"
TOKEN_UNK = "<unk>"
TOKEN_MASK = "<mask>"
TOKEN_CLS = "<cls>"
TOKEN_SEP = "<sep>"
TOKEN_NL = "<nl>" # Represent newline tokens clearly

# Map common tokenizer special attribute names to our constants
# This helps abstract away specific tokenizer implementations
SPECIAL_TOKEN_MAP = {
    "pad_token": TOKEN_PAD,
    "eos_token": TOKEN_EOS,
    "bos_token": TOKEN_BOS,
    "unk_token": TOKEN_UNK,
    "mask_token": TOKEN_MASK,
    "cls_token": TOKEN_CLS,
    "sep_token": TOKEN_SEP,
    # Add others as needed
}

# --- Keyboard Shortcuts ---
SHORTCUT_QUIT = "qqq" # Shortcut to quit the game (can be used at prompts)