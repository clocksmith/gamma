"""
Abstract base class for all model inference engines.

This provides a framework-agnostic interface that can be implemented
for different ML frameworks (PyTorch, JAX, TensorFlow, MLX, etc.) and
different model types (transformers, diffusion models, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    """Configuration for model engines."""

    model_name: str
    trust_remote_code: bool = False
    hf_token: Optional[str] = None
    verbose: bool = False
    seed: Optional[int] = None
    device_map: str = "auto"
    low_cpu_mem_usage: bool = True
    use_cache: bool = True

    # Additional engine-specific config
    extra: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, default)


class ModelEngine(ABC):
    """
    Abstract base class for all ML model engines.

    Provides a unified interface for:
    - Model loading/unloading
    - Inference
    - Configuration management
    - Device management
    - Caching

    Subclasses must implement model-specific inference logic.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.model: Any = None
        self._cache: Any = None
        self._device: Optional[str] = None

    # ========================================================================
    # Core Abstract Methods - Must be implemented by subclasses
    # ========================================================================

    @abstractmethod
    def load(self) -> None:
        """Load the model into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model from memory."""
        pass

    @abstractmethod
    def predict(self, inputs: Any, **kwargs) -> Dict[str, Any]:
        """
        Run inference on inputs.

        Args:
            inputs: Model-specific input format
            **kwargs: Additional inference parameters

        Returns:
            Dictionary containing prediction results
        """
        pass

    @abstractmethod
    def get_device(self) -> str:
        """Get device type (cpu, cuda, mps, etc)."""
        pass

    # ========================================================================
    # Common Helper Methods
    # ========================================================================

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None

    def _ensure_model_loaded(self):
        """Ensure model is loaded, raise error if not."""
        if not self.is_loaded():
            raise RuntimeError(
                f"{self.__class__.__name__}: Model not loaded. Call load() first."
            )

    def _error_model_not_loaded(self) -> RuntimeError:
        """Create standardized 'model not loaded' error."""
        return RuntimeError(
            f"{self.__class__.__name__}: Model not loaded. Call load() first."
        )

    # ========================================================================
    # Tensor Operations - Optional overrides for framework-specific behavior
    # ========================================================================

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """
        Convert framework-specific tensor to numpy array.

        Default implementation handles common cases.
        Override for framework-specific optimizations.
        """
        if isinstance(tensor, np.ndarray):
            return tensor

        # Handle PyTorch
        if hasattr(tensor, 'cpu') and hasattr(tensor, 'numpy'):
            return tensor.cpu().numpy()

        # Handle JAX
        if hasattr(tensor, '__array__'):
            return np.asarray(tensor)

        # Fallback
        return np.array(tensor)

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """
        Convert numpy array to framework-specific tensor.

        Override in subclasses for framework-specific conversion.
        """
        return array

    # ========================================================================
    # Cache Management
    # ========================================================================

    def has_cache(self) -> bool:
        """Check if cache exists."""
        return self._cache is not None

    def get_cache(self) -> Any:
        """Get current cache."""
        return self._cache

    def set_cache(self, cache: Any):
        """Set cache."""
        self._cache = cache

    def reset_cache(self) -> None:
        """Reset the cache to force full recomputation."""
        self._cache = None

    # ========================================================================
    # Configuration Helpers
    # ========================================================================

    def get_config_summary(self) -> Dict[str, Any]:
        """Get engine configuration summary for display."""
        return {
            "engine_class": self.__class__.__name__,
            "model_name": self.config.model_name,
            "device": self.get_device() if self.is_loaded() else "not loaded",
            **self.get_engine_specific_config()
        }

    def get_engine_specific_config(self) -> Dict[str, Any]:
        """Override in subclasses to provide engine-specific configuration."""
        return {}

    # ========================================================================
    # Logging and Debugging
    # ========================================================================

    def log_info(self, message: str):
        """Log info message with engine prefix."""
        logger.info(f"[{self.__class__.__name__}] {message}")

    def log_debug(self, message: str):
        """Log debug message with engine prefix."""
        if self.config.verbose:
            logger.debug(f"[{self.__class__.__name__}] {message}")

    def log_warning(self, message: str):
        """Log warning message with engine prefix."""
        logger.warning(f"[{self.__class__.__name__}] {message}")

    def log_error(self, message: str):
        """Log error message with engine prefix."""
        logger.error(f"[{self.__class__.__name__}] {message}")
