#!/usr/bin/env python3
"""Certify deterministic SABLE coverage activated by preceding context only."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "sable_precontext_consensus_qm0_v1"
EXPECTED_INPUT_BYTES = 587_138_826
EXPECTED_INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
GROSS_GATE_BYTES = 4_056_825
CONTROL_MARGIN_BYTES = 100_000
SOURCE_LIMIT_BYTES = 65_536
DECIMAL_LIMIT_KIB = 9_765_625
DONOR_PEAK_KIB = 10_438_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    try:
        label = str(resolved.relative_to(ROOT))
    except ValueError:
        label = str(resolved)
    return {
        "path": label,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def parse_intervals(path: Path) -> dict[str, int | bool]:
    payload = path.read_bytes()
    if len(payload) < 24 or payload[:8] != b"SABLEA1\0":
        raise ValueError("invalid SABLE interval header")
    records, declared_bytes = struct.unpack_from("<QQ", payload, 8)
    if len(payload) != 24 + records * 12:
        raise ValueError("SABLE interval file has inconsistent length")
    prior_end = 0
    observed = 0
    for index in range(records):
        start, length = struct.unpack_from("<QI", payload, 24 + index * 12)
        if not length or start < prior_end or start + length > EXPECTED_INPUT_BYTES:
            raise ValueError("SABLE intervals are not canonical and disjoint")
        prior_end = start + length
        observed += length
    if observed != declared_bytes:
        raise ValueError("SABLE interval byte total differs from header")
    return {
        "records": records,
        "declared_bytes": declared_bytes,
        "observed_bytes": observed,
        "canonical_disjoint_intervals": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/cmix_lex_payload_gate")
        / "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}"
    )
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    if args.input.stat().st_size != EXPECTED_INPUT_BYTES:
        raise ValueError("transformed-ready size differs from frozen input")
    if sha256_file(args.input) != EXPECTED_INPUT_SHA256:
        raise ValueError("transformed-ready SHA-256 differs from frozen input")

    source = ROOT / "tools/sable_precontext_consensus_qm0.cpp"
    binary = args.output_dir / "sable_precontext_consensus_qm0"
    build = subprocess.run(
        ["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source), "-o", str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"SABLE scanner build failed with status {build.returncode}")

    scans: list[dict[str, object]] = []
    interval_paths: list[Path] = []
    for suffix in ("a", "b"):
        interval_path = args.output_dir / f"addressable_{suffix}.bin"
        completed = subprocess.run(
            [str(binary), str(args.input), str(interval_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        (args.output_dir / f"scan_{suffix}.json").write_text(completed.stdout)
        (args.output_dir / f"scan_{suffix}.stderr.log").write_text(completed.stderr)
        if completed.returncode:
            raise RuntimeError(f"SABLE scan {suffix} failed with {completed.returncode}")
        scans.append(json.loads(completed.stdout))
        interval_paths.append(interval_path)

    interval_validation = parse_intervals(interval_paths[0])
    intervals_identical = interval_paths[0].read_bytes() == interval_paths[1].read_bytes()
    scans_identical = scans[0] == scans[1]
    scan = scans[0]
    distinct = int(scan["distinct_consensus_bytes"])
    shifted = int(scan["distinct_shifted37_bytes"])
    split = [int(value) for value in scan["split_distinct_consensus_bytes"]]

    source_paths = [
        Path(__file__),
        source,
        ROOT / "docs/sable_precontext_consensus_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_package_path = args.output_dir / "diagnostic_source_package.lzma"
    source_package_path.write_bytes(source_package)

    failed: list[str] = []
    if distinct < GROSS_GATE_BYTES:
        failed.append("eight_bit_absolute_ceiling_below_4056825")
    if any(value <= 0 for value in split):
        failed.append("chronological_third_without_consensus_coverage")
    if distinct - shifted < CONTROL_MARGIN_BYTES:
        failed.append("shifted37_control_margin_below_100000")
    if not scans_identical:
        failed.append("repeat_scan_summary_mismatch")
    if not intervals_identical:
        failed.append("repeat_interval_artifact_mismatch")
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("diagnostic_source_exceeds_65536")
    for field in (
        "all_sources_strictly_beyond_ring",
        "activation_uses_preceding_context_only",
        "target_bytes_excluded_from_activation",
        "all_hash_matches_exactly_verified",
    ):
        if not bool(scan[field]):
            failed.append(f"proof_failed_{field}")

    compact_state_bytes = int(scan["compact_minimum_resident_bytes"])
    donor_overage_kib = DONOR_PEAK_KIB - DECIMAL_LIMIT_KIB
    minimum_required_removal_kib = donor_overage_kib + (
        compact_state_bytes + 1023
    ) // 1024
    coverage_pass = distinct >= GROSS_GATE_BYTES
    verdict = (
        "authorize_exact_donor_surprise_certificate"
        if coverage_pass and not failed
        else "retire_deterministic_precontext_sable"
    )
    decision = {
        "schema": "enwiki9_sable_precontext_consensus_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "deterministic_precontext_consensus_impossibility_ceiling_zero_credit",
        "verdict": verdict,
        "inputs": {
            "transformed_ready": artifact(args.input),
            "parent_far_history_decision": artifact(
                ROOT / "results/cmix_obias_postwrt_far_history_cdc_qm0_v1/decision.json"
            ),
            "scanner_source": artifact(source),
            "scanner_binary": artifact(binary),
        },
        "gate": {
            "donor_score_debt_bytes": 3_492_825,
            "integration_allowance_bytes": 64_000,
            "transfer_reserve_bytes": 500_000,
            "gross_required_savings_bytes": GROSS_GATE_BYTES,
            "absolute_maximum_saved_bits_per_addressable_byte": 8,
            "minimum_distinct_addressable_bytes": GROSS_GATE_BYTES,
            "shifted37_control_margin_bytes": CONTROL_MARGIN_BYTES,
        },
        "scan": scan,
        "coverage_accounting": {
            "distinct_correct_consensus_bytes": distinct,
            "absolute_eight_bit_ceiling_bytes": distinct,
            "shortfall_to_gross_gate_bytes": max(0, GROSS_GATE_BYTES - distinct),
            "distinct_shifted37_control_bytes": shifted,
            "margin_over_shifted37_bytes": distinct - shifted,
            "donor_surprise_trace_required": coverage_pass,
            "score_credit_bytes": 0,
        },
        "memory_eligibility": {
            "strict_decimal_limit_kib": DECIMAL_LIMIT_KIB,
            "public_donor_peak_decode_kib": DONOR_PEAK_KIB,
            "donor_existing_overage_kib": donor_overage_kib,
            "compact_state_minimum_bytes": compact_state_bytes,
            "minimum_required_donor_memory_removal_kib": minimum_required_removal_kib,
            "identified_donor_memory_removal_kib": 0,
            "additive_native_implementation_currently_eligible": False,
        },
        "proof": {
            "receipt_bound_modeled_stream": True,
            "repeat_scan_summary_identical": scans_identical,
            "repeat_interval_artifact_identical": intervals_identical,
            **interval_validation,
            "strictly_beyond_ring_sources": bool(
                scan["all_sources_strictly_beyond_ring"]
            ),
            "preceding_context_activation_only": bool(
                scan["activation_uses_preceding_context_only"]
            ),
            "target_bytes_not_used_for_activation": bool(
                scan["target_bytes_excluded_from_activation"]
            ),
        },
        "artifacts": {
            "addressable_intervals": artifact(interval_paths[0]),
            "diagnostic_source_package": artifact(source_package_path),
        },
        "failed_conditions": failed,
        "claim_boundary": "Exact deterministic-consensus coverage ceiling on the external cmix-obias transformed stream. It prices no donor probabilities, proves no probabilistic low-entropy source gain, supplies no native expert, and receives zero score or forecast credit.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "distinct_consensus_bytes": distinct,
                "absolute_ceiling_shortfall_bytes": max(
                    0, GROSS_GATE_BYTES - distinct
                ),
                "shifted37_bytes": shifted,
                "failed_conditions": failed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
