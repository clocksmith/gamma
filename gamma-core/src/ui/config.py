"""UI configuration and color codes."""


class UIConfig:
    """Configuration for UI components."""

    # Color settings
    USE_COLORS = True

    # ANSI color codes
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_DIM = "\033[2m"

    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_YELLOW = "\033[93m"
    COLOR_BLUE = "\033[94m"
    COLOR_MAGENTA = "\033[95m"
    COLOR_CYAN = "\033[96m"
    COLOR_WHITE = "\033[97m"

    # Semantic colors
    COLOR_ERROR = COLOR_RED
    COLOR_SUCCESS = COLOR_GREEN
    COLOR_WARNING = COLOR_YELLOW
    COLOR_INFO = COLOR_BLUE
    COLOR_PROMPT = COLOR_CYAN

    # Display widths
    DISPLAY_WIDTH = 70
    INDENT_WIDTH = 2
