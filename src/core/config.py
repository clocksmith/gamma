import os
import sys

DEFAULT_ENGINE = "pytorch"
DEFAULT_MODEL_NAME = "google/gemma-3-1b-it"

# Gemma Model Information
GEMMA_MODEL_INFO = {
    "google/gemma-3-1b-it": {
        "desc": "1B, Instruct, versatile.",
        "params_b": 1.0,
        "raw_model_gb": 2.0,
        "rec_ram_gb": "4-6GB",
    },
    "google/gemma-3-4b-it": {
        "desc": "4B, Instruct, good balance.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
    "google/gemma-3-12b-it": {
        "desc": "12B, Instruct, powerful.",
        "params_b": 12.0,
        "raw_model_gb": 24.0,
        "rec_ram_gb": "32-48GB",
    },
    "google/gemma-3-27b-it": {
        "desc": "27B, Instruct, very strong.",
        "params_b": 27.0,
        "raw_model_gb": 54.0,
        "rec_ram_gb": "64-96GB",
    },
    "google/gemma-3-1b": {
        "desc": "1B, Base, for fine-tuning.",
        "params_b": 1.0,
        "raw_model_gb": 2.0,
        "rec_ram_gb": "4-6GB",
    },
    "google/gemma-3-4b": {
        "desc": "4B, Base.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
    "google/gemma-3-12b": {
        "desc": "12B, Base.",
        "params_b": 12.0,
        "raw_model_gb": 24.0,
        "rec_ram_gb": "32-48GB",
    },
    "google/gemma-3-27b": {
        "desc": "27B, Base, very large.",
        "params_b": 27.0,
        "raw_model_gb": 54.0,
        "rec_ram_gb": "64-96GB",
    },
    "google/gemma-3n-e4b-it": {
        "desc": "New 4B, Instruct, efficient.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
}

GEMMA_MODELS = list(GEMMA_MODEL_INFO.keys())

DEFAULT_GGUF_MODEL_PLACEHOLDER = "path/to/your/model.gguf"
DEFAULT_ONNX_MODEL_PLACEHOLDER = "path/to/your/model.onnx"
DEFAULT_MLX_MODEL_PLACEHOLDER = "mlx-community/Mistral-7B-Instruct-v0.2"

DEFAULT_TEMPERATURE = 0.9
DEFAULT_TOP_K = 64
DEFAULT_TOP_P = 0.95

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question directly in 1-2 sentences. "
    "Avoid repetition, avoid markdown, and use plain English."
)

DEFAULT_MAX_DECODE_STEPS = 8
DEFAULT_NUM_CHOICES = 4  # Number of multiple choice options (A, B, C, D)
DEFAULT_PERMUTATION_LENGTH = 1  # Number of tokens per choice (1 = single word/token)
DEFAULT_SHOW_ATTENTION = True
DEFAULT_VERBOSE = True
DEFAULT_FOCUS_WORDS = False
MIN_WORD_TOKEN_LENGTH = 2

MAX_TOKENS_FOR_PROB_DISPLAY = 10
USE_COLORS = True

PYTORCH_DEVICE_MAP = "auto"
PYTORCH_ATTN_IMPLEMENTATION = "eager"
PYTORCH_USE_KV_CACHE = False  # Disabled by default to avoid attention mask issues

LLAMA_CPP_N_GPU_LAYERS = 0
LLAMA_CPP_N_CTX = 2048
LLAMA_CPP_LIB_VERBOSE = False

ONNX_PROVIDERS = ["CPUExecutionProvider"]
ONNX_PROVIDER_OPTIONS = None

JAX_DTYPE = "float32"
MLX_LOAD_CONFIG = {}

if os.name == "nt":
    try:
        import colorama
        colorama.init()
    except ImportError:
        if os.environ.get("TERM") not in [
            "xterm", "xterm-color", "xterm-256color", "linux", "screen", "vt100", "rxvt", "putty",
        ]:
            USE_COLORS = False
elif not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
    USE_COLORS = False

if USE_COLORS:
    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_BLUE = "\033[94m"
    COLOR_YELLOW = "\033[93m"
    COLOR_CYAN = "\033[96m"
    COLOR_BOLD = "\033[1m"
    COLOR_RESET = "\033[0m"
    COLOR_MAGENTA_DIM = "\033[38;5;54m"
    COLOR_MAGENTA_LIGHT = "\033[38;5;91m"
    COLOR_MAGENTA_MEDIUM = "\033[38;5;127m"
    COLOR_MAGENTA_BRIGHT = "\033[38;5;164m"
    COLOR_MAGENTA_INTENSE = "\033[38;5;201m"
else:
    COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_CYAN = "", "", "", "", ""
    COLOR_BOLD = ""
    COLOR_MAGENTA_DIM, COLOR_MAGENTA_LIGHT, COLOR_MAGENTA_MEDIUM = "", "", ""
    COLOR_MAGENTA_BRIGHT, COLOR_MAGENTA_INTENSE, COLOR_RESET = "", "", ""

TOKEN_PAD = "<pad>"
TOKEN_EOS = "<eos>"
TOKEN_BOS = "<bos>"
TOKEN_UNK = "<unk>"
TOKEN_MASK = "<mask>"
TOKEN_CLS = "<cls>"
TOKEN_SEP = "<sep>"
TOKEN_NL = "<nl>"

SPECIAL_TOKEN_GAME_REPR = {
    "pad_token": TOKEN_PAD,
    "eos_token": TOKEN_EOS,
    "bos_token": TOKEN_BOS,
    "unk_token": TOKEN_UNK,
    "mask_token": TOKEN_MASK,
    "cls_token": TOKEN_CLS,
    "sep_token": TOKEN_SEP,
}

SHORTCUT_QUIT = "q" # Changed from "qqq"
SHORTCUT_CONFIRM_CONFIG_ACCEPT = "y"
SHORTCUT_CONFIRM_CONFIG_MODIFY = "m"
SHORTCUT_MODIFY_PARAM_SKIP = ""
