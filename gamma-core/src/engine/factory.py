"""
Engine factory for creating engine instances.

Handles engine registration, discovery, and instantiation.
"""

from typing import Dict, Type, Optional, List
from .base import ModelEngine, EngineConfig
import logging

logger = logging.getLogger(__name__)


class EngineFactory:
    """Factory for creating and managing engine instances."""

    _engines: Dict[str, Type[ModelEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_class: Type[ModelEngine]):
        """Register an engine class with a name."""
        cls._engines[name] = engine_class
        logger.debug(f"Registered engine: {name} -> {engine_class.__name__}")

    @classmethod
    def create(cls, name: str, config: EngineConfig) -> ModelEngine:
        """Create an engine instance by name."""
        if name not in cls._engines:
            available = ", ".join(cls._engines.keys())
            raise ValueError(
                f"Unknown engine '{name}'. Available engines: {available}"
            )

        engine_class = cls._engines[name]
        return engine_class(config)

    @classmethod
    def list_engines(cls) -> List[str]:
        """List all registered engines."""
        return list(cls._engines.keys())

    @classmethod
    def has_engine(cls, name: str) -> bool:
        """Check if an engine is registered."""
        return name in cls._engines

    @classmethod
    def get_engine_class(cls, name: str) -> Optional[Type[ModelEngine]]:
        """Get engine class by name."""
        return cls._engines.get(name)
