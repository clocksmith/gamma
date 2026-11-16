"""Use an explicit gamma-core checkout, the adjacent repository, or its installed package."""
import os
from pathlib import Path
import sys


def configure_gamma_core_path():
    override = os.environ.get("GAMMA_CORE_SRC_PATH", "").strip()
    source = Path(override).expanduser().resolve() if override else Path(__file__).resolve().parents[4] / "gamma-core" / "src"
    if override and not source.is_dir():
        raise ModuleNotFoundError(f"GAMMA_CORE_SRC_PATH is not a directory: {source}")
    if source.is_dir() and str(source) not in sys.path:
        sys.path.insert(0, str(source))
    # Otherwise normal imports resolve the declared installed gamma-core dependency.
    return source if source.is_dir() else None
