"""
Basic UI components for the GAMMA application.
"""

import textwrap
from src.core import config as cfg

def color_text(text: str, color_code: str) -> str:
    """Applies color codes to text for terminal output."""
    return f"{color_code}{text}{cfg.COLOR_RESET}" if cfg.USE_COLORS and color_code else text

def print_separator(char: str = "=", length: int = 70):
    """Prints a separator line."""
    print(char * length)

def print_header(title: str):
    """Prints a formatted header."""
    print("\n")
    print_separator()
    print(f" {title} ".center(70, "="))
    print_separator()

def wrap_print(text: str, indent: str = "", width: int = 70, initial_indent_add: str = ""):
    """Wraps and prints text to the console."""
    actual_initial_indent = indent + initial_indent_add
    normalized_text = " ".join(text.split())
    lines = textwrap.wrap(normalized_text, width=width, initial_indent=actual_initial_indent, subsequent_indent=indent)
    for line in lines:
        print(line)
