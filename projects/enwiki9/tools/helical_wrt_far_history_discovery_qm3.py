#!/usr/bin/env python3
"""Run exact event-aligned far-history discovery directly on full WRT."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "helical_wrt_far_history_discovery_qm3_v1"
GUARD = ROOT / "tools/run_with_rss_guard.py"
STORE_SHA = "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"
DEBT = 4_389_323
RESERVE = 500_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def guarded(binary: Path, store: Path, output_dir: Path, suffix: str):
    ledger = output_dir / f"ledger_{suffix}.bin"
    guard_path = output_dir / f"scan_{suffix}.guard.json"
    command = [sys.executable, str(GUARD), "--limit-kib", "10485760",
               "--limit-mode", "max_single", "--official-decimal-limit-kib", "9765625",
               "--sample-interval", "0.5", "--guard-json", str(guard_path),
               "--label", f"{CANDIDATE_ID}_{suffix}", str(binary), str(store), str(ledger)]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, check=False)
    (output_dir / f"scan_{suffix}.stdout.log").write_text(completed.stdout)
    (output_dir / f"scan_{suffix}.stderr.log").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"scan {suffix} failed with {completed.returncode}")
    scan, _ = json.JSONDecoder().raw_decode(completed.stdout.lstrip())
    return scan, json.loads(guard_path.read_text()), ledger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path(
        "/home/x/enwiki9-nonproof/results/helical_far_history_wrt_event_map_qm2_v1/enwik9.store"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if sha256_file(args.store) != STORE_SHA:
        raise ValueError("full WRT store hash mismatch")
    source = ROOT / "tools/helical_wrt_far_history_discovery_qm3.cpp"
    binary = args.output_dir / "helical_wrt_far_history_discovery_qm3"
    build = subprocess.run(["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source),
                            "-o", str(binary)], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, check=False)
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"build failed with {build.returncode}")
    scan_a, guard_a, ledger_a = guarded(binary, args.store, args.output_dir, "a")
    scan_b, guard_b, ledger_b = guarded(binary, args.store, args.output_dir, "b")
    ledger_bytes = ledger_a.read_bytes()
    deterministic = scan_a == scan_b and ledger_bytes == ledger_b.read_bytes()
    packed = lzma.compress(ledger_bytes, preset=9 | lzma.PRESET_EXTREME)
    packed_path = args.output_dir / "ledger.lzma"
    packed_path.write_bytes(packed)
    source_paths = [Path(__file__), source,
                    ROOT / "docs/helical_wrt_far_history_discovery_qm3_plan.md",
                    ROOT / f"programs/{CANDIDATE_ID}/meta.json"]
    source_package = lzma.compress(b"".join(
        p.name.encode() + b"\0" + p.read_bytes() for p in source_paths),
        preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "source_package.lzma"
    source_path.write_bytes(source_package)
    gross = float(scan_a["average_rate_gross_bytes"])
    paid_margin = gross - len(packed) - len(source_package) - DEBT
    free_reserve_margin = gross - DEBT - RESERVE
    failed = []
    if not deterministic:
        failed.append("scan_or_ledger_nondeterministic")
    if any(int(value) <= 0 for value in scan_a["split_copied_wrt_bytes"]):
        failed.append("coded_third_without_copy")
    if free_reserve_margin < 0:
        failed.append("free_gross_below_debt_plus_reserve")
    for label, guard in (("a", guard_a), ("b", guard_b)):
        if int(guard.get("official_decimal_over_limit_kib", 0)):
            failed.append(f"scan_{label}_decimal_memory_failed")
    verdict = "authorize_wrt_corridor_optimization" if not failed else "retire_wrt_far_history_universe"
    if not failed and paid_margin >= 0:
        verdict = "authorize_paid_wrt_residual_integration"
    decision = {
        "schema": "enwiki9_helical_wrt_far_history_discovery_qm3_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_parent_coordinate_representation_ceiling_zero_credit",
        "verdict": verdict,
        "inputs": {"wrt_store": artifact(args.store), "scanner_source": artifact(source),
                   "scanner_binary": artifact(binary),
                   "parent_qm2": artifact(ROOT / "results/helical_far_history_wrt_event_map_qm2_v1/decision.json")},
        "scan": scan_a,
        "finite_ledger": {"raw": artifact(ledger_a), "compressed": artifact(packed_path),
                          "source_package": artifact(source_path)},
        "accounting": {"gross_proxy_bytes": gross, "compressed_ledger_bytes": len(packed),
                       "source_package_bytes": len(source_package), "debt_bytes": DEBT,
                       "paid_bare_margin_bytes": paid_margin,
                       "free_margin_after_debt_and_500k_reserve_bytes": free_reserve_margin,
                       "score_credit_bytes": 0},
        "proof": {"deterministic_repeat": deterministic,
                  "event_aligned": bool(scan_a["all_selected_spans_event_aligned"]),
                  "exact_prior_closed": bool(scan_a["all_selected_spans_exact_prior_and_closed"])},
        "resources": {"scan_a_guard": guard_a, "scan_b_guard": guard_b},
        "failed_conditions": failed,
        "claim_boundary": (
            "Exact full-WRT event-aligned far-history discovery and finite collective ledger. Gross uses the "
            "Endpoint428 archive-average WRT rate, not an actual P1 span trace. No residual archive, raw inverse "
            "receipt, official score, or forecast update is claimed."),
    }
    (args.output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "matches": scan_a["selected_matches"],
                      "copied_wrt_bytes": scan_a["copied_wrt_bytes"],
                      "gross_proxy_bytes": gross, "ledger_lzma_bytes": len(packed),
                      "paid_bare_margin": paid_margin, "free_reserve_margin": free_reserve_margin,
                      "failed_conditions": failed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
