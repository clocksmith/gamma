#!/usr/bin/env python3
"""Run the exact MOIRAI v1 WRT-prefix falsification screen."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs" / "moirai_wrt_syndrome_v1" / "program.py"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_program() -> Any:
    spec = importlib.util.spec_from_file_location("moirai_v1", PROGRAM)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load MOIRAI candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args: argparse.Namespace) -> dict[str, Any]:
    source = args.input.read_bytes()
    data = source[args.offset : args.offset + args.limit]
    if len(data) != args.limit:
        raise ValueError("input does not cover requested screen window")
    module = load_program()
    started = time.monotonic()
    analysis = module.analyze(data)
    elapsed = time.monotonic() - started
    source_gzip = len(gzip.compress(PROGRAM.read_bytes(), compresslevel=9))
    roundtrip = analysis["roundtrip"]
    exact = all(roundtrip.values())
    deltas = analysis["deltas"]
    reverse_beats_forward = deltas["bidirectional_minus_forward_bytes"] < 0
    reverse_beats_causal = deltas["bidirectional_minus_causal_bytes"] < 0
    verdict = (
        "viable_for_larger_exact_gate"
        if exact and reverse_beats_forward and reverse_beats_causal
        else "retire_bidirectional_energy_v1"
        if exact and not reverse_beats_forward
        else "retire_syndrome_coder_v1"
        if exact
        else "invalid_roundtrip"
    )
    return {
        "schema": "moirai_wrt_syndrome_screen_v1",
        "evidence_level": "constructive_prefix",
        "candidate_id": "moirai_wrt_syndrome_v1",
        "claim_boundary": (
            "Exact bounded WRT-prefix coder comparison only. This is not a "
            "page-complete model, target-strength backend, native endpoint "
            "replacement, transferable score, or full-corpus proof."
        ),
        "input": {
            "path": str(args.input.resolve()),
            "source_bytes": len(source),
            "offset": args.offset,
            "scope_bytes": len(data),
            "scope_sha256": sha256(data),
        },
        "implementation": {
            "path": str(PROGRAM.relative_to(ROOT)),
            "bytes": PROGRAM.stat().st_size,
            "gzip9_bytes": source_gzip,
            "block_bits": module.BLOCK_BITS,
            "model_order": module.MODEL_ORDER,
            "reverse_weight": module.REVERSE_WEIGHT,
            "weight_scale": module.WEIGHT_SCALE,
        },
        "analysis": analysis,
        "runtime": {
            "combined_screen_elapsed_seconds": elapsed,
        },
        "decision": {
            "verdict": verdict,
            "promotion_authorized": verdict == "viable_for_larger_exact_gate",
            "score_credit_bytes": 0,
            "reason": (
                "Promotion requires the bidirectional exact archive to beat "
                "both forward-only syndrome inference and matched causal "
                "coding before source cost."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"missing input: {args.input}")
    if args.offset < 0 or args.limit <= 0:
        raise SystemExit("offset must be nonnegative and limit must be positive")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "verdict": receipt["decision"]["verdict"],
                "roundtrip": receipt["analysis"]["roundtrip"],
                "deltas": receipt["analysis"]["deltas"],
                "runtime_seconds": receipt["runtime"][
                    "combined_screen_elapsed_seconds"
                ],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
