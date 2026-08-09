#!/usr/bin/env python3
"""Map frozen HELICAL spans onto exact full-1G WRT events and distance floors."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "helical_far_history_wrt_event_map_qm2_v1"
GUARD = ROOT / "tools/run_with_rss_guard.py"
RAW_SHA = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
STORE_SHA = "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"
C1_SHA = "2f35bfe0d84f14a82f6e47aba4a810fcf5a1f71a0eea08391456adb071487e1f"
DICT_SHA = "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"
ENDPOINT_ARCHIVE_FORECAST = 109_128_198
ENDPOINT_DEBT = 4_389_323
FRAMING = 64


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def guarded(binary: Path, raw: Path, store: Path, dictionary: Path, c1: Path,
            output_dir: Path, suffix: str):
    prefix = output_dir / suffix
    guard_path = output_dir / f"map_{suffix}.guard.json"
    command = [sys.executable, str(GUARD), "--limit-kib", "10485760",
               "--limit-mode", "max_single", "--official-decimal-limit-kib", "9765625",
               "--sample-interval", "0.5", "--guard-json", str(guard_path),
               "--label", f"{CANDIDATE_ID}_{suffix}", str(binary), str(raw), str(store),
               str(dictionary), str(c1), str(prefix)]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, check=False)
    (output_dir / f"map_{suffix}.stdout.log").write_text(completed.stdout)
    (output_dir / f"map_{suffix}.stderr.log").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"map {suffix} failed with {completed.returncode}")
    scan, _ = json.JSONDecoder().raw_decode(completed.stdout.lstrip())
    paths = {arm: {column: Path(f"{prefix}.{arm}.{column}")
                   for column in ("gaps", "modes", "opens", "shifts", "lengths")}
             for arm in ("endpoint", "cmix")}
    return scan, json.loads(guard_path.read_text()), paths


def compress_arm(paths: dict[str, Path], output_dir: Path, arm: str):
    columns = {}
    total = FRAMING
    for name, path in paths.items():
        payload = path.read_bytes()
        packed = lzma.compress(payload, preset=9 | lzma.PRESET_EXTREME)
        packed_path = output_dir / f"{arm}_{name}.lzma"
        packed_path.write_bytes(packed)
        total += len(packed)
        columns[name] = {"raw_bytes": len(payload), "lzma_bytes": len(packed),
                         "artifact": artifact(packed_path)}
    return {"columns": columns, "framing_bytes": FRAMING, "command_bytes": total}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--store", type=Path, default=Path(
        "/home/x/enwiki9-nonproof/results/helical_far_history_wrt_event_map_qm2_v1/enwik9.store"))
    parser.add_argument("--dictionary", type=Path,
                        default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--c1", type=Path,
                        default=ROOT / "results/helical_far_history_corridor_qm0_v1/c1_a.bin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    expected = ((args.raw, RAW_SHA), (args.store, STORE_SHA),
                (args.dictionary, DICT_SHA), (args.c1, C1_SHA))
    if any(sha256_file(path) != digest for path, digest in expected):
        raise ValueError("input binding failed")
    source = ROOT / "tools/helical_far_history_wrt_event_map_qm2.cpp"
    binary = args.output_dir / "helical_far_history_wrt_event_map_qm2"
    build = subprocess.run(["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source),
                            "-o", str(binary)], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, check=False)
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"build failed with {build.returncode}")
    scan_a, guard_a, paths_a = guarded(binary, args.raw, args.store, args.dictionary,
                                       args.c1, args.output_dir, "a")
    scan_b, guard_b, paths_b = guarded(binary, args.raw, args.store, args.dictionary,
                                       args.c1, args.output_dir, "b")
    deterministic = scan_a == scan_b and all(
        paths_a[arm][name].read_bytes() == paths_b[arm][name].read_bytes()
        for arm in paths_a for name in paths_a[arm])
    endpoint_commands = compress_arm(paths_a["endpoint"], args.output_dir, "endpoint")
    cmix_commands = compress_arm(paths_a["cmix"], args.output_dir, "cmix")
    source_paths = [Path(__file__), source,
                    ROOT / "docs/helical_far_history_wrt_event_map_qm2_plan.md",
                    ROOT / f"programs/{CANDIDATE_ID}/meta.json"]
    source_package = lzma.compress(b"".join(
        p.name.encode() + b"\0" + p.read_bytes() for p in source_paths),
        preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "source_package.lzma"
    source_path.write_bytes(source_package)
    endpoint = scan_a["endpoint100m"]
    gross = (int(endpoint["wrt_bytes"]) * ENDPOINT_ARCHIVE_FORECAST /
             int(scan_a["wrt_stream_bytes"]))
    bare_margin = gross - int(endpoint_commands["command_bytes"]) - len(source_package) - ENDPOINT_DEBT
    reserve_margin = bare_margin - 500_000
    failed = []
    if not deterministic:
        failed.append("mapping_or_columns_nondeterministic")
    if any(int(value) <= 0 for value in endpoint["split_wrt_bytes"]):
        failed.append("endpoint_population_missing_chronological_third")
    if bare_margin < 0:
        failed.append("endpoint_average_rate_bare_target_inequality_failed")
    for label, guard in (("a", guard_a), ("b", guard_b)):
        if int(guard.get("official_decimal_over_limit_kib", 0)):
            failed.append(f"map_{label}_decimal_memory_failed")
    decision = {
        "schema": "enwiki9_helical_far_history_wrt_event_map_qm2_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_exact_wrt_compatibility_zero_credit",
        "verdict": "authorize_endpoint_full_p1_span_trace" if not failed else "retire_endpoint_wrt_far_history_realization",
        "inputs": {"raw": artifact(args.raw), "wrt_store": artifact(args.store),
                   "dictionary": artifact(args.dictionary), "frozen_c1": artifact(args.c1),
                   "mapper_source": artifact(source), "mapper_binary": artifact(binary)},
        "scan": scan_a,
        "finite_commands": {"endpoint100m": endpoint_commands, "cmix60m": cmix_commands,
                            "source_package_bytes": len(source_package)},
        "endpoint_average_rate_accounting": {
            "wrt_copied_bytes": endpoint["wrt_bytes"], "gross_proxy_bytes": gross,
            "command_bytes": endpoint_commands["command_bytes"],
            "source_package_bytes": len(source_package), "debt_bytes": ENDPOINT_DEBT,
            "bare_margin_bytes": bare_margin, "margin_with_500k_reserve_bytes": reserve_margin,
            "score_credit_bytes": 0},
        "proof": {"full_wrt_inverse_exact": bool(scan_a["full_wrt_inverse_exact"]),
                  "all_selected_wrt_spans_exact_equal": bool(scan_a["all_selected_wrt_spans_exact_equal"]),
                  "deterministic_repeat": deterministic},
        "resources": {"map_a_guard": guard_a, "map_b_guard": guard_b},
        "artifacts": {"source_package": artifact(source_path)},
        "failed_conditions": failed,
        "claim_boundary": (
            "Exact full-1G WRT inverse, raw-to-event alignment, encoded-span equality, and parent-stream distance audit. "
            "Endpoint gross remains an archive-average proxy until a full P1 trace prices these exact intervals. "
            "The 60M arm is compatibility evidence only because cmix-obias uses a different modeled stream. Score credit is zero."),
    }
    (args.output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": decision["verdict"],
                      "event_aligned_raw_bytes": scan_a["event_aligned_raw_bytes"],
                      "encoded_equal_raw_bytes": scan_a["encoded_equal_raw_bytes"],
                      "endpoint_matches": endpoint["matches"],
                      "endpoint_wrt_bytes": endpoint["wrt_bytes"],
                      "endpoint_command_bytes": endpoint_commands["command_bytes"],
                      "endpoint_bare_margin": bare_margin,
                      "endpoint_reserve_margin": reserve_margin,
                      "failed_conditions": failed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
