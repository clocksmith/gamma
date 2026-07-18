#!/usr/bin/env python3
"""Materialize and seal an exact WikiIR prefix for target-backend probes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("wikiir_materialized_program", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load WikiIR program: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(input_path: Path, scope_bytes: int, program_path: Path) -> tuple[bytes, dict[str, Any]]:
    if scope_bytes < 1:
        raise ValueError("scope must be positive")
    with input_path.open("rb") as stream:
        raw = stream.read(scope_bytes)
    if len(raw) != scope_bytes:
        raise ValueError("input is shorter than the declared scope")
    module = load_module(program_path)
    encode_ir = getattr(module, "encode_ir", None)
    decode_ir = getattr(module, "decode_ir", None)
    if not callable(encode_ir) or not callable(decode_ir):
        raise RuntimeError("WikiIR program must expose encode_ir and decode_ir")
    first_ir, first_stats = encode_ir(raw)
    second_ir, second_stats = encode_ir(raw)
    if not isinstance(first_ir, bytes) or not isinstance(first_stats, dict):
        raise RuntimeError("encode_ir returned an invalid result")
    roundtrip_ok = decode_ir(first_ir) == raw
    determinism_ok = first_ir == second_ir and first_stats == second_stats
    if not roundtrip_ok or not determinism_ok:
        raise RuntimeError("WikiIR roundtrip or determinism failed")
    receipt = {
        "schema": "wikiir_materialization_v1",
        "evidence_level": "exact_reversible_representation_prefix",
        "scope_bytes": scope_bytes,
        "input": {
            "path": str(input_path.resolve()),
            "scoped_sha256": sha256_bytes(raw),
        },
        "program": {
            "path": str(program_path.resolve()),
            "bytes": program_path.stat().st_size,
            "sha256": sha256(program_path),
        },
        "ir": {
            "bytes": len(first_ir),
            "sha256": sha256_bytes(first_ir),
        },
        "stats": first_stats,
        "identity": {
            "raw_ir_roundtrip_ok": roundtrip_ok,
            "encode_ir_deterministic": determinism_ok,
        },
        "claim_boundary": "Representation evidence only; no backend or official-score claim.",
    }
    return first_ir, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--program", type=Path, required=True)
    parser.add_argument("--output-ir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    ir, receipt = run(args.input, args.scope_bytes, args.program)
    args.output_ir.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary_ir = args.output_ir.with_suffix(args.output_ir.suffix + ".tmp")
    temporary_receipt = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
    temporary_ir.write_bytes(ir)
    receipt["ir"]["path"] = str(args.output_ir.resolve())
    temporary_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary_ir, args.output_ir)
    os.replace(temporary_receipt, args.receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
