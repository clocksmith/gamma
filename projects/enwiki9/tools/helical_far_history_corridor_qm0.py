#!/usr/bin/env python3
"""Run the frozen HELICAL bounded-source corridor command audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "helical_far_history_corridor_qm0_v1"
GUARD = ROOT / "tools/run_with_rss_guard.py"
DECIMAL_LIMIT_KIB = 9_765_625
EXPECTED_INPUT_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
EXPECTED_LEDGER_SHA256 = "580cca00014f02e425b10692afc33e817259d9ab4b6fcc953201ea48aa5f0cf8"
EXPECTED_M0_BYTES = 4_058_323
ENDPOINT_GROSS_PROXY = 7_041_620
ENDPOINT_DEBT = 4_389_323
CMIX_GROSS_PROXY = 6_969_452
CMIX_DEBT = 3_492_825
RESERVE_BYTES = 500_000


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


def run_guarded(binary: Path, input_path: Path, ledger: Path, output_dir: Path,
                suffix: str) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    c0 = output_dir / f"c0_{suffix}.bin"
    c1 = output_dir / f"c1_{suffix}.bin"
    stdout_path = output_dir / f"scan_{suffix}.json"
    stderr_path = output_dir / f"scan_{suffix}.stderr.log"
    guard_path = output_dir / f"scan_{suffix}.guard.json"
    command = [
        sys.executable, str(GUARD),
        "--limit-kib", "10485760",
        "--limit-mode", "max_single",
        "--official-decimal-limit-kib", str(DECIMAL_LIMIT_KIB),
        "--sample-interval", "0.5",
        "--guard-json", str(guard_path),
        "--label", f"{CANDIDATE_ID}_{suffix}",
        str(binary), str(input_path), str(ledger), str(c0), str(c1),
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, check=False)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"guarded scan {suffix} failed with {completed.returncode}")
    scan, _ = json.JSONDecoder().raw_decode(completed.stdout.lstrip())
    return scan, json.loads(guard_path.read_text()), c0, c1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument(
        "--ledger", type=Path,
        default=ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/ledger_a.bin",
    )
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if sha256_file(args.input) != EXPECTED_INPUT_SHA256:
        raise ValueError("canonical input hash mismatch")
    if sha256_file(args.ledger) != EXPECTED_LEDGER_SHA256:
        raise ValueError("frozen ledger hash mismatch")

    source = ROOT / "tools/helical_far_history_corridor_qm0.cpp"
    binary = args.output_dir / "helical_far_history_corridor_qm0"
    build = subprocess.run(
        ["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source), "-o", str(binary)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False,
    )
    (args.output_dir / "build.log").write_text(build.stdout, encoding="utf-8")
    if build.returncode:
        raise RuntimeError(f"build failed with {build.returncode}")

    scan_a, guard_a, c0_a, c1_a = run_guarded(
        binary, args.input, args.ledger, args.output_dir, "a")
    scan_b, guard_b, c0_b, c1_b = run_guarded(
        binary, args.input, args.ledger, args.output_dir, "b")
    c0_payload = c0_a.read_bytes()
    c1_payload = c1_a.read_bytes()
    c0_repeat = c0_b.read_bytes()
    c1_repeat = c1_b.read_bytes()
    c0_compressed = lzma.compress(c0_payload, preset=9 | lzma.PRESET_EXTREME)
    c1_compressed = lzma.compress(c1_payload, preset=9 | lzma.PRESET_EXTREME)
    c0_lzma = args.output_dir / "c0_commands.lzma"
    c1_lzma = args.output_dir / "c1_commands.lzma"
    c0_lzma.write_bytes(c0_compressed)
    c1_lzma.write_bytes(c1_compressed)

    source_paths = [
        Path(__file__), source,
        ROOT / "docs/helical_far_history_corridor_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_package_path = args.output_dir / "source_package.lzma"
    source_package_path.write_bytes(source_package)

    c1_cost = len(c1_compressed) + len(source_package)
    endpoint_margin = ENDPOINT_GROSS_PROXY - c1_cost - ENDPOINT_DEBT - RESERVE_BYTES
    cmix_margin = CMIX_GROSS_PROXY - c1_cost - CMIX_DEBT - RESERVE_BYTES
    failed: list[str] = []
    if int(scan_a["m0_inline_bytes"]) != EXPECTED_M0_BYTES:
        failed.append("m0_does_not_reproduce_4058323")
    if scan_a != scan_b:
        failed.append("repeat_scan_summary_mismatch")
    if c0_payload != c0_repeat:
        failed.append("repeat_c0_stream_mismatch")
    if c1_payload != c1_repeat:
        failed.append("repeat_c1_stream_mismatch")
    if int(scan_a["c0_address_bytes"]) >= int(scan_a["cs_address_bytes"]):
        failed.append("real_c0_does_not_beat_shuffled_control")
    if len(c1_compressed) >= 3_296_268:
        failed.append("c1_does_not_beat_existing_collective_ledger")
    if endpoint_margin < 0 and cmix_margin < 0:
        failed.append("proxy_target_inequality_fails_for_both_parents")
    for guard_name, guard in (("a", guard_a), ("b", guard_b)):
        if int(guard.get("official_decimal_over_limit_kib", 0)) > 0:
            failed.append(f"scan_{guard_name}_decimal_memory_failed")

    decision = {
        "schema": "enwiki9_helical_far_history_corridor_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_corridor_command_audit_zero_credit",
        "verdict": "authorize_parent_span_pricing" if not failed else "retire_bounded_corridor_realization",
        "inputs": {
            "canonical_input": artifact(args.input),
            "frozen_match_ledger": artifact(args.ledger),
            "parent_decision": artifact(
                ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/decision.json"),
            "scanner_source": artifact(source),
            "scanner_binary": artifact(binary),
        },
        "scan": scan_a,
        "finite_commands": {
            "d0_existing_collective_lzma_bytes": 3_296_268,
            "c0_raw_bytes": len(c0_payload),
            "c0_lzma_bytes": len(c0_compressed),
            "c1_raw_bytes": len(c1_payload),
            "c1_lzma_bytes": len(c1_compressed),
            "compressed_source_package_bytes": len(source_package),
        },
        "proxy_accounting": {
            "warning": "Average-rate proxies only; actual parent selected-span costs remain unmeasured.",
            "reserve_bytes": RESERVE_BYTES,
            "endpoint428_gross_proxy_bytes": ENDPOINT_GROSS_PROXY,
            "endpoint428_debt_bytes": ENDPOINT_DEBT,
            "endpoint428_proxy_margin_after_c1_source_reserve_bytes": endpoint_margin,
            "cmix_obias_gross_proxy_bytes": CMIX_GROSS_PROXY,
            "cmix_obias_debt_bytes": CMIX_DEBT,
            "cmix_obias_proxy_margin_after_c1_source_reserve_bytes": cmix_margin,
            "score_credit_bytes": 0,
        },
        "proof": {
            "m0_exactly_reproduced": int(scan_a["m0_inline_bytes"]) == EXPECTED_M0_BYTES,
            "all_candidates_exact": bool(scan_a["all_candidates_exact"]),
            "all_sources_strictly_prior": bool(scan_a["all_sources_strictly_prior"]),
            "all_sources_fully_closed": bool(scan_a["all_sources_fully_closed"]),
            "scan_summary_deterministic": scan_a == scan_b,
            "c0_stream_deterministic": c0_payload == c0_repeat,
            "c1_stream_deterministic": c1_payload == c1_repeat,
            "real_geometry_beats_shuffled": int(scan_a["c0_address_bytes"]) < int(scan_a["cs_address_bytes"]),
        },
        "resources": {"scan_a_guard": guard_a, "scan_b_guard": guard_b},
        "artifacts": {
            "c0_commands": artifact(c0_a),
            "c0_commands_lzma": artifact(c0_lzma),
            "c1_commands": artifact(c1_a),
            "c1_commands_lzma": artifact(c1_lzma),
            "source_package": artifact(source_package_path),
        },
        "failed_conditions": failed,
        "claim_boundary": (
            "Exact full-1G bounded-alternative address and command audit over the frozen target intervals. "
            "Every real source is collision-verified and prior. The shuffled arm is a noncodec geometry control. "
            "Average-rate parent arithmetic is diagnostic only; this receipt is not an Endpoint428 or cmix replay, "
            "does not yet use implicit CDC extents, and earns no score credit."
        ),
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": decision["verdict"],
        "m0_inline_bytes": scan_a["m0_inline_bytes"],
        "alternatives": scan_a["alternative_candidates"],
        "c0_corridors": scan_a["c0_corridors"],
        "c0_lzma_bytes": len(c0_compressed),
        "c1_lzma_bytes": len(c1_compressed),
        "endpoint_proxy_margin": endpoint_margin,
        "cmix_proxy_margin": cmix_margin,
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
