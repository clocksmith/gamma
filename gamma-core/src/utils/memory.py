"""Memory monitoring utilities."""

import psutil
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.

    Returns:
        Dictionary with:
        - rss_mb: Resident set size in MB
        - vms_mb: Virtual memory size in MB
        - percent: Memory usage percentage
    """
    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "rss_mb": memory_info.rss / 1024 / 1024,
        "vms_mb": memory_info.vms / 1024 / 1024,
        "percent": process.memory_percent()
    }


def log_memory_usage(prefix: str = ""):
    """Log current memory usage."""
    stats = get_memory_usage()
    message = f"{prefix}Memory: {stats['rss_mb']:.1f}MB RSS, {stats['percent']:.1f}%"
    logger.info(message)
    return stats
