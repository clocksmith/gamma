#!/usr/bin/env python3
"""Seal an encode-side WikiIR target-backend economics screen."""

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


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("wikiir_probe_program", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load WikiIR program: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_guard(guard: dict[str, Any]) -> bool:
    limit = int(guard.get("official_decimal_limit_kib", 0))
    return bool(
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("limit_mode") == "tree"
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
        and limit > 0
        and int(guard.get("max_sampled_tree_rss_kib", limit + 1)) <= limit
    )


def run(
    *,
    input_path: Path,
    scope_bytes: int,
    ir_path: Path,
    wikiir_program: Path,
    backend: Path,
    dictionary: Path,
    baseline_archive: Path,
    candidate_archive: Path,
    guard_path: Path,
) -> dict[str, Any]:
    if scope_bytes < 1:
        raise ValueError("invalid probe scope")
    with input_path.open("rb") as stream:
        raw = stream.read(scope_bytes)
    if len(raw) != scope_bytes:
        raise ValueError("input is shorter than the declared scope")
    ir = ir_path.read_bytes()
    module = load_module(wikiir_program)
    if not callable(getattr(module, "decode_ir", None)):
        raise RuntimeError("WikiIR program lacks decode_ir")
    raw_ir_roundtrip_ok = module.decode_ir(ir) == raw
    if not raw_ir_roundtrip_ok:
        raise RuntimeError("WikiIR inverse does not reconstruct the scoped input")

    guard = json.loads(guard_path.read_text())
    if not isinstance(guard, dict) or not clean_guard(guard):
        raise RuntimeError("target-backend encode guard is not clean")
    expected_command = [
        str(backend.resolve()),
        "-c",
        str(dictionary.resolve()),
        str(ir_path.resolve()),
        str(candidate_archive.resolve()),
    ]
    if guard.get("command") != expected_command:
        raise RuntimeError("guard command differs from the declared target-backend probe")

    baseline = baseline_archive.read_bytes()
    candidate = candidate_archive.read_bytes()
    # Both artifacts are direct cmix archives and each already contains its
    # native input/block header.  Comparing a full candidate archive with a
    # header-stripped baseline overcharged the candidate by 37 bytes.
    archive_delta = len(candidate) - len(baseline)
    receipt = {
        "schema": "wikiir_target_backend_probe_v2",
        "evidence_level": "encode_side_exact_target_backend_economics_screen",
        "scope": {
            "raw_bytes": len(raw),
            "ir_bytes": len(ir),
            "raw_ir_delta_bytes": len(raw) - len(ir),
        },
        "artifacts": {
            "input": {
                "path": str(input_path.resolve()),
                "scoped_bytes": len(raw),
                "scoped_sha256": sha256_bytes(raw),
            },
            "ir": artifact(ir_path),
            "wikiir_program": artifact(wikiir_program),
            "backend": artifact(backend),
            "dictionary": artifact(dictionary),
            "baseline_archive": artifact(baseline_archive),
            "candidate_archive": artifact(candidate_archive),
            "encode_guard": artifact(guard_path),
        },
        "metrics": {
            "baseline_target_backend_archive_bytes": len(baseline),
            "wikiir_target_backend_archive_bytes": len(candidate),
            "wikiir_archive_delta_bytes": archive_delta,
            "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "official_decimal_limit_kib": guard["official_decimal_limit_kib"],
            "decimal_margin_kib": (
                guard["official_decimal_limit_kib"]
                - guard["max_sampled_tree_rss_kib"]
            ),
        },
        "identity": {
            "raw_ir_roundtrip_ok": raw_ir_roundtrip_ok,
            "target_backend_encode_guard_clean": True,
            "complete_native_archive_comparison": True,
            "backend_decode_not_run_after_terminal_archive_miss": archive_delta > 0,
        },
        "verdict": (
            "retire_representation_on_target_backend_archive_miss"
            if archive_delta >= 0
            else "target_backend_archive_headroom_requires_full_roundtrip"
        ),
        "promotion_authorized": False,
        "next_action": (
            "Move to a different WikiIR event universe; do not tune or scale the "
            "measured serialization."
            if archive_delta >= 0
            else "Run guarded backend decode, raw inverse, determinism, disjoint, and counted-code gates."
        ),
        "claim_boundary": (
            "The raw-to-IR inverse is exact and the target-backend encode archive is "
            "exact at the measured prefix. Backend archive decode was intentionally "
            "not run after a terminal archive-size miss. This is negative discovery "
            "evidence, not a score or full codec proof."
        ),
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--wikiir-program", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--baseline-archive", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(
        input_path=args.input,
        scope_bytes=args.scope_bytes,
        ir_path=args.ir,
        wikiir_program=args.wikiir_program,
        backend=args.backend,
        dictionary=args.dictionary,
        baseline_archive=args.baseline_archive,
        candidate_archive=args.candidate_archive,
        guard_path=args.guard,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
