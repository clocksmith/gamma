"""Basic UI components for terminal applications."""

import textwrap
from .config import UIConfig


def color_text(text: str, color_code: str) -> str:
    """Applies color codes to text for terminal output."""
    if UIConfig.USE_COLORS and color_code:
        return f"{color_code}{text}{UIConfig.COLOR_RESET}"
    return text


def print_separator(char: str = "=", length: int = 70):
    """Prints a separator line."""
    print(char * length)


def print_header(title: str):
    """Prints a formatted header."""
    print("\n")
    print_separator()
    print(f" {title} ".center(70, "="))
    print_separator()


def wrap_print(
    text: str,
    indent: str = "",
    width: int = 70,
    initial_indent_add: str = ""
):
    """Wraps and prints text to the console."""
    actual_initial_indent = indent + initial_indent_add
    normalized_text = " ".join(text.split())
    lines = textwrap.wrap(
        normalized_text,
        width=width,
        initial_indent=actual_initial_indent,
        subsequent_indent=indent
    )
    for line in lines:
        print(line)
