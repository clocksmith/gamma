"""Terminal components with Gamma's color configuration."""

from gamma.core import config as cfg
from gamma.core.gamma_core_adapter import print_header, print_separator, wrap_print

__all__ = ["color_text", "print_header", "print_separator", "wrap_print"]


def color_text(text: str, color_code: str) -> str:
    """Applies color codes to text for terminal output."""
    return f"{color_code}{text}{cfg.COLOR_RESET}" if cfg.USE_COLORS and color_code else text
