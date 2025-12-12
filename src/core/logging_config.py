"""
Centralized logging configuration for GAMMA.

Provides consistent logging setup across all modules with support for
different verbosity levels and output formats.

Usage:
    from src.core.logging_config import setup_logging, get_logger

    # In main entry point:
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # In modules:
    logger = get_logger(__name__)
    logger.info("Processing...")
"""

import logging
import sys
from typing import Optional


# Package-level logger name prefix
LOGGER_PREFIX = "gamma"

# Default format strings
DEFAULT_FORMAT = "%(levelname)s - %(name)s - %(message)s"
VERBOSE_FORMAT = "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s"
QUIET_FORMAT = "%(message)s"

# Color codes for terminal output
_COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m'
}


class ColoredFormatter(logging.Formatter):
    """Formatter that adds ANSI color codes for terminal output."""

    def __init__(self, fmt: str, use_color: bool = True):
        super().__init__(fmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = _COLORS.get(record.levelname, '')
            reset = _COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None,
    use_color: bool = True
) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable DEBUG level and detailed format
        quiet: Only show WARNING and above, minimal format
        log_file: Optional file path to write logs to
        use_color: Use ANSI colors in terminal output

    Note:
        - verbose takes precedence over quiet if both are True
        - log_file output is always without color
    """
    # Determine log level and format
    if verbose:
        level = logging.DEBUG
        fmt = VERBOSE_FORMAT
    elif quiet:
        level = logging.WARNING
        fmt = QUIET_FORMAT
    else:
        level = logging.INFO
        fmt = DEFAULT_FORMAT

    # Configure root logger for our package
    root_logger = logging.getLogger(LOGGER_PREFIX)
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(fmt, use_color=use_color))
    root_logger.addHandler(console_handler)

    # File handler (if requested)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    _configure_third_party_loggers(quiet)


def _configure_third_party_loggers(quiet: bool) -> None:
    """Reduce noise from common third-party libraries."""
    noisy_loggers = [
        'transformers',
        'transformers.tokenization_utils_base',
        'transformers.modeling_utils',
        'torch',
        'urllib3',
        'filelock',
        'huggingface_hub',
    ]

    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING if not quiet else logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Logger configured under the gamma hierarchy

    Usage:
        logger = get_logger(__name__)
        logger.debug("Detailed info")
        logger.info("General info")
        logger.warning("Warning message")
        logger.error("Error message")
    """
    # If name starts with 'src.', replace with our prefix
    if name.startswith('src.'):
        name = f"{LOGGER_PREFIX}.{name[4:]}"
    elif not name.startswith(LOGGER_PREFIX):
        name = f"{LOGGER_PREFIX}.{name}"

    return logging.getLogger(name)


def set_level(level: int) -> None:
    """
    Change the logging level at runtime.

    Args:
        level: logging.DEBUG, logging.INFO, logging.WARNING, etc.
    """
    root_logger = logging.getLogger(LOGGER_PREFIX)
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


def add_file_handler(filepath: str, level: int = logging.DEBUG) -> logging.Handler:
    """
    Add a file handler at runtime.

    Args:
        filepath: Path to log file
        level: Minimum level for this handler

    Returns:
        The created handler (for later removal if needed)
    """
    handler = logging.FileHandler(filepath)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))

    logging.getLogger(LOGGER_PREFIX).addHandler(handler)
    return handler


# Convenience aliases for common log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
