#!/usr/bin/env python3
"""Constructive VULCAN event-PPM control over the canonical 10M WRT stream."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import lzma
from pathlib import Path
from types import ModuleType

import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal5_vulcan_event_parent_control_qm0_v1"
VULCAN_PATH = ROOT / "programs/vulcan_event_ppm_v1/program.py"


def load_vulcan() -> ModuleType:
    spec = importlib.util.spec_from_file_location("fractal5_vulcan_program", VULCAN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load VULCAN program")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path,
                        default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--wrt-store", type=Path,
                        default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"))
    parser.add_argument("--dictionary", type=Path,
                        default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--parent-archive", type=Path,
                        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/archive.bin")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw = args.raw_input.read_bytes()
    parsed = wrt_exact.parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise RuntimeError("canonical WRT store does not invert to raw input")
    vulcan = load_vulcan()

    archive_a = vulcan.compress(parsed.stream)
    stats_a = dict(vulcan.stats())
    restored = vulcan.decompress(archive_a)
    archive_b = vulcan.compress(parsed.stream)
    stats_b = dict(vulcan.stats())
    exact_stream = restored == parsed.stream
    deterministic = archive_a == archive_b
    (args.output_dir / "archive_a.bin").write_bytes(archive_a)
    (args.output_dir / "archive_b.bin").write_bytes(archive_b)

    source_paths = [Path(__file__), VULCAN_PATH, Path(wrt_exact.__file__)]
    source_blob = b"".join(path.name.encode("ascii") + b"\0" + path.read_bytes()
                           for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    parent_bytes = args.parent_archive.stat().st_size
    event_archive_bytes = len(archive_a)
    gap = event_archive_bytes - parent_bytes
    counted_control = event_archive_bytes + len(source_package)
    failed: list[str] = []
    if not exact_stream:
        failed.append("WRT_stream_roundtrip_failed")
    if not deterministic:
        failed.append("second_archive_not_identical")
    if gap > 250000:
        failed.append("event_archive_gap_above_250000_bytes")
    if float(stats_a.get("decision_reduction", 0.0)) < 0.5:
        failed.append("event_decision_reduction_below_50_percent")

    decision = {
        "schema": "enwiki9_fractal5_vulcan_event_parent_control_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "constructive_alternate_wrt_codec_zero_credit",
        "verdict": "authorize_form_conditioned_event_gate" if not failed else "retire_vulcan_form_route",
        "inputs": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256(raw),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_stream_sha256": sha256(parsed.stream),
            "parent_archive_bytes": parent_bytes,
            "parent_archive_sha256": hashlib.sha256(args.parent_archive.read_bytes()).hexdigest(),
        },
        "event_control": {
            "archive_bytes": event_archive_bytes,
            "archive_sha256": sha256(archive_a),
            "second_archive_bytes": len(archive_b),
            "second_archive_sha256": sha256(archive_b),
            "gap_vs_endpoint428_bytes": gap,
            "stats_first": stats_a,
            "stats_second": stats_b,
        },
        "proof": {
            "WRT_stream_roundtrip_exact": exact_stream,
            "raw_inverse_exact_by_identical_canonical_WRT_stream": exact_stream and parsed.decoded == raw,
            "second_archive_identical": deterministic,
        },
        "accounting": {
            "event_archive_bytes": event_archive_bytes,
            "source_package_bytes": len(source_package),
            "counted_control_bytes": counted_control,
            "endpoint428_state_updates_integrated": False,
            "score_credit_bytes": 0,
        },
        "failed_conditions": failed,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "event_archive_bytes": event_archive_bytes,
        "parent_archive_bytes": parent_bytes,
        "gap_vs_endpoint428_bytes": gap,
        "decision_reduction": stats_a.get("decision_reduction"),
        "proof": decision["proof"],
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(args.output_dir / "decision.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
