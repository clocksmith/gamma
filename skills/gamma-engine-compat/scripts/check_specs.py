#!/usr/bin/env python3
"""
Validate GAMMA model specs in batch, optionally enforcing logits support.
"""

from __future__ import annotations

import argparse
import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.core.model_validator import ModelValidator  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Validate engine:model specs for GAMMA.")
    ap.add_argument("specs", nargs="+", help="Model specs in engine:model format.")
    ap.add_argument(
        "--require-logits",
        action="store_true",
        help="Fail specs that do not expose raw logits.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    any_fail = False

    for spec in args.specs:
        result = ModelValidator.validate_model_spec(spec, require_logits=args.require_logits)
        if result.is_valid:
            print(f"[OK]   {spec}")
            if result.warning_message:
                print(f"  warning: {result.warning_message}")
            if result.suggestion:
                print(f"  suggestion: {result.suggestion}")
            continue

        any_fail = True
        print(f"[FAIL] {spec}")
        if result.error_message:
            print(f"  error: {result.error_message}")
        if result.suggestion:
            print(f"  suggestion: {result.suggestion}")

    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
