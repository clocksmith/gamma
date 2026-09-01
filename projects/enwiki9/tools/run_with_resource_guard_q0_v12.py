#!/usr/bin/env python3
"""V12 zero-swap identity guard, source-bound directly by the v12 preflight."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
V11_PATH = PROJECT / "tools/run_with_resource_guard_q0_v11.py"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V11 = _load(V11_PATH, "cmix_q0_v12_guard_v11_base")


def main() -> int:
    return V11.main()


if __name__ == "__main__":
    raise SystemExit(main())
