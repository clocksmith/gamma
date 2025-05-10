import os
import sys

DEFAULT_ENGINE = "pytorch"
DEFAULT_MODEL_NAME = "google/gemma-2-2b-it"

DEFAULT_GGUF_MODEL_PLACEHOLDER = "path/to/your/model.gguf"
DEFAULT_ONNX_MODEL_PLACEHOLDER = "path/to/your/model.onnx"
DEFAULT_MLX_MODEL_PLACEHOLDER = "mlx-community/Mistral-7B-Instruct-v0.2"

DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 8
DEFAULT_TOP_P = 0.95

DEFAULT_MAX_DECODE_STEPS = 8
DEFAULT_NUM_CHOICES = 4
DEFAULT_PERMUTATION_LENGTH = 3
DEFAULT_SHOW_ATTENTION = True
DEFAULT_VERBOSE = True
DEFAULT_FOCUS_WORDS = False
MIN_WORD_TOKEN_LENGTH = 2

MAX_TOKENS_FOR_PROB_DISPLAY = 10
USE_COLORS = True

PYTORCH_DEVICE_MAP = "auto"
PYTORCH_ATTN_IMPLEMENTATION = "eager"
PYTORCH_USE_KV_CACHE = True

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
    COLOR_RESET = "\033[0m"
    COLOR_MAGENTA_DIM = "\033[38;5;54m"
    COLOR_MAGENTA_LIGHT = "\033[38;5;91m"
    COLOR_MAGENTA_MEDIUM = "\033[38;5;127m"
    COLOR_MAGENTA_BRIGHT = "\033[38;5;164m"
    COLOR_MAGENTA_INTENSE = "\033[38;5;201m"
else:
    COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_CYAN = "", "", "", "", ""
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