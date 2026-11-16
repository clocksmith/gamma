"""
Shared verbose logging mixin for Mind Meld components.

Provides a consistent _log() method that routes to proper logger
with verbosity-aware log levels.
"""

import logging

logger = logging.getLogger(__name__)


class VerboseLoggerMixin:
    """
    Mixin that provides a consistent _log() method for verbose output.

    Classes using this mixin should have a `verbose` attribute.
    When verbose=True, messages are logged at INFO level.
    When verbose=False, messages are logged at DEBUG level.

    Usage:
        class MyClass(VerboseLoggerMixin):
            def __init__(self, verbose: bool = False):
                self.verbose = verbose

            def some_method(self):
                self._log("Processing started")  # Uses logger appropriately
    """

    def _log(self, message: str) -> None:
        """
        Log a message with appropriate level based on verbose setting.

        Args:
            message: Message to log. Class name prefix is added automatically.
        """
        formatted = f"[{self.__class__.__name__}] {message}"
        if getattr(self, 'verbose', False):
            logger.info(formatted)
        else:
            logger.debug(formatted)

    def _log_warning(self, message: str) -> None:
        """
        Log a warning message (always shown regardless of verbose setting).

        Args:
            message: Warning message to log.
        """
        formatted = f"[{self.__class__.__name__}] {message}"
        logger.warning(formatted)

    def _log_error(self, message: str) -> None:
        """
        Log an error message (always shown regardless of verbose setting).

        Args:
            message: Error message to log.
        """
        formatted = f"[{self.__class__.__name__}] {message}"
        logger.error(formatted)
