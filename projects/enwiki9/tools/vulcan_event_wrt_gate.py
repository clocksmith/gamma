#!/usr/bin/env python3
"""Run a VULCAN candidate on an exact, receipt-bound WRT store."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import time
from types import ModuleType
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def load_candidate(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("vulcan_gate_candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import candidate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("compress", "decompress", "stats"):
        if not hasattr(module, name):
            raise ValueError(f"candidate lacks {name}()")
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--store-receipt", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--promotion-penalty", type=int, default=5_000)
    parser.add_argument("--kill-penalty", type=int, default=15_000)
    parser.add_argument("--minimum-decision-reduction", type=float, default=0.50)
    args = parser.parse_args()

    store_receipt = json.loads(args.store_receipt.read_text())
    baseline_manifest = json.loads(args.baseline_manifest.read_text())
    store = args.store.read_bytes()
    expected_store_hash = str(store_receipt["sha256"])
    actual_store_hash = sha256_bytes(store)
    if actual_store_hash != expected_store_hash:
        raise ValueError("WRT store hash does not match its receipt")
    raw_hash = sha256_file(args.raw)
    if raw_hash != str(baseline_manifest["raw_sha256"]):
        raise ValueError("raw hash does not match baseline manifest")

    candidate = load_candidate(args.candidate)
    encode_started = time.perf_counter()
    archive = candidate.compress(store)
    encode_seconds = time.perf_counter() - encode_started
    first_stats = candidate.stats()

    decode_started = time.perf_counter()
    restored = candidate.decompress(archive)
    decode_seconds = time.perf_counter() - decode_started
    roundtrip_ok = restored == store

    second_started = time.perf_counter()
    second_archive = candidate.compress(store)
    second_encode_seconds = time.perf_counter() - second_started
    deterministic = second_archive == archive

    baseline_bytes = int(baseline_manifest["compressed_size"])
    penalty = len(archive) - baseline_bytes
    decision_reduction = float(first_stats.get("decision_reduction", 0.0))
    promotion_pass = (
        roundtrip_ok
        and deterministic
        and penalty <= args.promotion_penalty
        and decision_reduction >= args.minimum_decision_reduction
    )
    kill = (
        not roundtrip_ok
        or not deterministic
        or penalty > args.kill_penalty
        or decision_reduction < args.minimum_decision_reduction
    )
    if promotion_pass:
        decision = "promote_to_native_event_rate_integration"
    elif kill:
        decision = "retire_vulcan_event_ppm_v1"
    else:
        decision = "retain_as_runtime_primitive_only"

    receipt = {
        "schema": "vulcan_event_wrt_gate/v1",
        "evidence_level": "constructive_wrt_store_gate",
        "candidate": artifact(args.candidate),
        "inputs": {
            "wrt_store": artifact(args.store),
            "wrt_store_receipt": artifact(args.store_receipt),
            "raw": artifact(args.raw),
            "baseline_manifest": artifact(args.baseline_manifest),
        },
        "scope": {
            "raw_bytes": args.raw.stat().st_size,
            "wrt_bytes": len(store),
            "baseline_archive_bytes": baseline_bytes,
        },
        "result": {
            "archive_bytes": len(archive),
            "archive_sha256": sha256_bytes(archive),
            "archive_delta_vs_baseline_bytes": penalty,
            "restored_wrt_sha256": sha256_bytes(restored),
            "roundtrip_ok": roundtrip_ok,
            "deterministic_second_archive": deterministic,
            "second_archive_sha256": sha256_bytes(second_archive),
            "encode_seconds": encode_seconds,
            "decode_seconds": decode_seconds,
            "second_encode_seconds": second_encode_seconds,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "candidate_stats": first_stats,
        },
        "gate": {
            "promotion_max_archive_penalty_bytes": args.promotion_penalty,
            "kill_archive_penalty_bytes": args.kill_penalty,
            "minimum_decision_reduction": args.minimum_decision_reduction,
            "promotion_pass": promotion_pass,
            "kill": kill,
            "decision": decision,
        },
        "claim_boundary": (
            "This is an exact transformed-store candidate gate, not a full raw "
            "enwik9 archive or full-corpus Hutter score."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt["gate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
