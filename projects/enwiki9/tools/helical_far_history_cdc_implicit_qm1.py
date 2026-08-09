#!/usr/bin/env python3
"""Measure HELICAL with decoder-rebuilt CDC extents on frozen C1 sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "helical_far_history_cdc_implicit_qm1_v1"
GUARD = ROOT / "tools/run_with_rss_guard.py"
INPUT_SHA = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
C1_SHA = "2f35bfe0d84f14a82f6e47aba4a810fcf5a1f71a0eea08391456adb071487e1f"
ENDPOINT_RATE_NUMERATOR = 109_128_198
ENDPOINT_DEBT = 4_389_323
CMIX_ARCHIVE = 108_009_834
CMIX_DEBT = 3_492_825
RESERVE = 500_000
FRAMING_BYTES = 64


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def guarded(binary: Path, input_path: Path, c1: Path, output_dir: Path,
            suffix: str) -> tuple[dict[str, object], dict[str, object], dict[str, Path]]:
    names = ("bitset", "gaps", "counts", "address_modes", "opens", "shifts")
    paths = {name: output_dir / f"{name}_{suffix}.bin" for name in names}
    guard_path = output_dir / f"scan_{suffix}.guard.json"
    command = [
        sys.executable, str(GUARD), "--limit-kib", "10485760",
        "--limit-mode", "max_single", "--official-decimal-limit-kib", "9765625",
        "--sample-interval", "0.5", "--guard-json", str(guard_path),
        "--label", f"{CANDIDATE_ID}_{suffix}", str(binary), str(input_path), str(c1),
        *(str(paths[name]) for name in names),
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, check=False)
    (output_dir / f"scan_{suffix}.stdout.log").write_text(completed.stdout)
    (output_dir / f"scan_{suffix}.stderr.log").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"scan {suffix} failed with {completed.returncode}")
    scan, _ = json.JSONDecoder().raw_decode(completed.stdout.lstrip())
    return scan, json.loads(guard_path.read_text()), paths


def compress_columns(paths: dict[str, Path], output_dir: Path) -> tuple[dict[str, object], int, str]:
    compressed: dict[str, bytes] = {}
    rows: dict[str, object] = {}
    for name, path in paths.items():
        payload = path.read_bytes()
        packed = lzma.compress(payload, preset=9 | lzma.PRESET_EXTREME)
        compressed[name] = packed
        packed_path = output_dir / f"{name}.lzma"
        packed_path.write_bytes(packed)
        rows[name] = {"raw_bytes": len(payload), "lzma_bytes": len(packed),
                      "artifact": artifact(packed_path)}
    bitset_total = (len(compressed["bitset"]) + len(compressed["address_modes"]) +
                    len(compressed["opens"]) + len(compressed["shifts"]) +
                    FRAMING_BYTES)
    run_total = (len(compressed["gaps"]) + len(compressed["counts"]) +
                 len(compressed["address_modes"]) + len(compressed["opens"]) +
                 len(compressed["shifts"]) + FRAMING_BYTES)
    if bitset_total <= run_total:
        return rows, bitset_total, "bitset"
    return rows, run_total, "run_columns"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--c1", type=Path,
                        default=ROOT / "results/helical_far_history_corridor_qm0_v1/c1_a.bin")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if sha256_file(args.input) != INPUT_SHA or sha256_file(args.c1) != C1_SHA:
        raise ValueError("frozen input binding failed")
    source = ROOT / "tools/helical_far_history_cdc_implicit_qm1.cpp"
    binary = args.output_dir / "helical_far_history_cdc_implicit_qm1"
    build = subprocess.run(["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source),
                            "-o", str(binary)], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, check=False)
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"build failed with {build.returncode}")
    scan_a, guard_a, paths_a = guarded(binary, args.input, args.c1, args.output_dir, "a")
    scan_b, guard_b, paths_b = guarded(binary, args.input, args.c1, args.output_dir, "b")
    deterministic_columns = all(
        paths_a[name].read_bytes() == paths_b[name].read_bytes() for name in paths_a)
    columns, command_bytes, schedule = compress_columns(paths_a, args.output_dir)
    source_paths = [Path(__file__), source,
                    ROOT / "docs/helical_far_history_cdc_implicit_qm1_plan.md",
                    ROOT / f"programs/{CANDIDATE_ID}/meta.json"]
    source_blob = b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "source_package.lzma"
    source_path.write_bytes(source_package)
    copied = int(scan_a["copied_bytes"])
    endpoint_gross = copied * ENDPOINT_RATE_NUMERATOR / 1_000_000_000
    cmix_gross = copied * CMIX_ARCHIVE / 1_000_000_000
    counted_commands = command_bytes + len(source_package)
    endpoint_margin = endpoint_gross - counted_commands - ENDPOINT_DEBT - RESERVE
    cmix_margin = cmix_gross - counted_commands - CMIX_DEBT - RESERVE
    failed: list[str] = []
    if scan_a != scan_b:
        failed.append("scan_summary_nondeterministic")
    if not deterministic_columns:
        failed.append("command_columns_nondeterministic")
    if any(int(v) <= 0 for v in scan_a["split_copied_bytes"]):
        failed.append("chronological_third_without_copy")
    if command_bytes >= 3_175_732:
        failed.append("implicit_commands_do_not_beat_columnar_c1")
    if endpoint_margin < 0 and cmix_margin < 0:
        failed.append("proxy_target_inequality_fails_for_both_parents")
    for label, guard in (("a", guard_a), ("b", guard_b)):
        if int(guard.get("official_decimal_over_limit_kib", 0)):
            failed.append(f"scan_{label}_decimal_memory_failed")
    decision = {
        "schema": "enwiki9_helical_far_history_cdc_implicit_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_implicit_chunk_command_audit_zero_credit",
        "verdict": "authorize_exact_parent_span_pricing" if not failed else "retire_implicit_cdc_realization",
        "inputs": {"canonical_input": artifact(args.input), "frozen_c1": artifact(args.c1),
                   "parent_decision": artifact(ROOT / "results/helical_far_history_corridor_qm0_v1/decision.json"),
                   "scanner_source": artifact(source), "scanner_binary": artifact(binary)},
        "scan": scan_a,
        "finite_commands": {"columns": columns, "selected_schedule": schedule,
                            "framing_bytes": FRAMING_BYTES,
                            "command_bytes": command_bytes,
                            "source_package_bytes": len(source_package),
                            "counted_command_and_source_bytes": counted_commands},
        "proxy_accounting": {
            "warning": "Average-rate diagnostic only; no parent span trace has been measured.",
            "endpoint428_gross_bytes": endpoint_gross,
            "endpoint428_margin_after_debt_commands_source_reserve_bytes": endpoint_margin,
            "cmix_obias_gross_bytes": cmix_gross,
            "cmix_obias_margin_after_debt_commands_source_reserve_bytes": cmix_margin,
            "reserve_bytes": RESERVE, "score_credit_bytes": 0},
        "proof": {"scan_deterministic": scan_a == scan_b,
                  "columns_deterministic": deterministic_columns,
                  "decoder_visible_source_boundaries": bool(scan_a["all_source_boundaries_decoder_visible"]),
                  "all_chunks_exact_prior_and_closed": bool(scan_a["all_chunks_exact_prior_and_closed"])},
        "resources": {"scan_a_guard": guard_a, "scan_b_guard": guard_b},
        "artifacts": {"source_package": artifact(source_path)},
        "failed_conditions": failed,
        "claim_boundary": (
            "Exact full-1G command audit over complete decoder-rebuilt CDC chunks inside the frozen C1 spans. "
            "It charges the selected schedule, address modes, openings, shifts, framing, and source. Parent gain "
            "remains average-rate evidence until an archive-identical state-preserving span trace exists; score credit is zero."),
    }
    (args.output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": decision["verdict"], "copied_bytes": copied,
                      "command_bytes": command_bytes, "schedule": schedule,
                      "endpoint_margin": endpoint_margin, "cmix_margin": cmix_margin,
                      "failed_conditions": failed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
