#!/usr/bin/env python3
"""Compatibility entrypoint shim for legacy path.

This module forwards execution to the relocated implementation under
projects/distillation/ while emitting a deprecation warning.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "projects" / "distillation").is_dir():
            return candidate
    raise RuntimeError("Unable to resolve repository root for compatibility shim.")


def _target_script() -> Path:
    return _repo_root() / "projects" / "distillation" / "embedding" / "eval" / "run_eval.py"


def main() -> int:
    target = _target_script()
    print(
        f"[DEPRECATED] {Path(__file__).as_posix()} is deprecated. "
        f"Use {target.as_posix()} instead.",
        file=sys.stderr,
    )
    return subprocess.call([sys.executable, str(target), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
