"""Fail-closed scientific harness for cross-model KV-cache transfer.

This package is intentionally independent from Mind Meld's production swap
loop.  It does not expose textual replay, cache reset, or heuristic fallback.
"""

from .contract import (
    CacheGeometry,
    CacheLayout,
    ContractError,
    ExperimentContract,
    ModelIdentity,
    RopeContract,
    RouteOutcome,
)
from .hf_cache import LBSHDCache
from .mapper import DirectionalMapper

__all__ = [
    "CacheGeometry",
    "CacheLayout",
    "ContractError",
    "DirectionalMapper",
    "ExperimentContract",
    "LBSHDCache",
    "ModelIdentity",
    "RopeContract",
    "RouteOutcome",
]
