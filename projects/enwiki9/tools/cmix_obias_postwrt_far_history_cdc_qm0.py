#!/usr/bin/env python3
"""Price exact copies beyond cmix-obias's post-WRT 60M byte history ring."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_postwrt_far_history_cdc_qm0_v1"
EXPECTED_INPUT_BYTES = 587_138_826
EXPECTED_INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
DONOR_PAYLOAD_BYTES = 107_726_514
DONOR_TOTAL_SCORE_BYTES = 108_492_825
INTEGRATION_ALLOWANCE_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validate_ledger(payload: bytes, expected_records: int) -> dict[str, int | bool]:
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("bad collective ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != expected_records:
        raise ValueError("ledger record count differs from scan")
    if 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("ledger component lengths do not cover payload")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    counts = tuple(
        sum(byte & 128 == 0 for byte in column)
        for column in (
            payload[40:gap_end],
            payload[gap_end:distance_end],
            payload[distance_end:],
        )
    )
    return {
        "records": records,
        "raw_bytes": len(payload),
        "gap_stream_bytes": gap_size,
        "distance_stream_bytes": distance_size,
        "length_stream_bytes": length_size,
        "component_record_counts_equal": counts == (records, records, records),
    }


def generated_scanner(parent_source: str) -> str:
    replacements = {
        "constexpr uint64_t kExpectedSize = 1000000000ULL;":
            "constexpr uint64_t kExpectedSize = 587138826ULL;",
        "constexpr uint64_t kMinimumDistance = 100000000ULL;":
            "constexpr uint64_t kMinimumDistance = 60000000ULL;",
        "constexpr uint64_t kArchiveOnlyForecast = 109128198ULL;":
            "constexpr uint64_t kArchiveOnlyForecast = 107726514ULL;",
    }
    generated = parent_source
    for old, new in replacements.items():
        if generated.count(old) != 1:
            raise ValueError(f"scanner source replacement contract failed: {old}")
        generated = generated.replace(old, new)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/cmix_lex_payload_gate/")
        / "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    if args.input.stat().st_size != EXPECTED_INPUT_BYTES:
        raise ValueError("transformed-ready input has wrong size")
    if sha256_file(args.input) != EXPECTED_INPUT_SHA256:
        raise ValueError("transformed-ready input has wrong SHA-256")

    parent_source = ROOT / "tools/far_history_cdc_collective_ledger_qm1.cpp"
    generated_source = args.output_dir / "cmix_obias_postwrt_far_history_cdc_qm0.cpp"
    generated_source.write_text(generated_scanner(parent_source.read_text()))
    binary = args.output_dir / "cmix_obias_postwrt_far_history_cdc_qm0"
    build = subprocess.run(
        ["g++", "-O3", "-DNDEBUG", "-std=c++17", str(generated_source), "-o", str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"scanner build failed with status {build.returncode}")

    scans: list[dict[str, object]] = []
    ledgers: list[bytes] = []
    ledger_paths: list[Path] = []
    for suffix in ("a", "b"):
        ledger_path = args.output_dir / f"ledger_{suffix}.bin"
        completed = subprocess.run(
            [str(binary), str(args.input), str(ledger_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        (args.output_dir / f"scan_{suffix}.json").write_text(completed.stdout)
        (args.output_dir / f"scan_{suffix}.stderr.log").write_text(completed.stderr)
        if completed.returncode:
            raise RuntimeError(f"scanner {suffix} failed with status {completed.returncode}")
        scans.append(json.loads(completed.stdout))
        ledgers.append(ledger_path.read_bytes())
        ledger_paths.append(ledger_path)

    scan = scans[0]
    validation = validate_ledger(ledgers[0], int(scan["selected_matches"]))
    compressed_a = lzma.compress(ledgers[0], preset=9 | lzma.PRESET_EXTREME)
    compressed_b = lzma.compress(ledgers[1], preset=9 | lzma.PRESET_EXTREME)
    compressed_path = args.output_dir / "ledger.lzma"
    compressed_path.write_bytes(compressed_a)

    source_paths = [
        Path(__file__),
        parent_source,
        ROOT / "docs/cmix_obias_postwrt_far_history_cdc_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)

    gross = float(scan["average_rate_equivalent_gross_bytes"])
    net = gross - len(compressed_a) - INTEGRATION_ALLOWANCE_BYTES
    copied = int(scan["copied_bytes"])
    split_copied = [int(value) for value in scan["split_copied_bytes"]]
    failed: list[str] = []
    if copied < 40_000_000:
        failed.append("copied_bytes_below_40000000")
    if net < 4_500_000:
        failed.append("payload_rate_net_below_4500000")
    if any(value <= 0 for value in split_copied):
        failed.append("stream_third_without_selected_copy")
    if scans[0] != scans[1]:
        failed.append("repeat_scan_summary_mismatch")
    if ledgers[0] != ledgers[1]:
        failed.append("repeat_raw_ledger_mismatch")
    if compressed_a != compressed_b:
        failed.append("repeat_compressed_ledger_mismatch")
    if not bool(validation["component_record_counts_equal"]):
        failed.append("ledger_parse_validation_failed")
    if len(source_package) > INTEGRATION_ALLOWANCE_BYTES:
        failed.append("diagnostic_source_exceeds_integration_allowance")
    for field in (
        "selected_sources_strictly_prior",
        "selected_sources_fully_closed",
        "selected_anchors_exactly_verified",
    ):
        if not bool(scan[field]):
            failed.append(f"proof_failed_{field}")

    decision = {
        "schema": "enwiki9_cmix_obias_postwrt_far_history_cdc_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "external_parent_postwrt_representation_ceiling_zero_credit",
        "verdict": "authorize_native_cmix_obias_integration" if not failed else "retire_postwrt_far_history_copy",
        "inputs": {
            "transformed_ready": artifact(args.input),
            "construction_receipt": artifact(ROOT / "results/cmix_lex_payload_transfer_v1_retry2/decision.json"),
            "parent_scanner_source": artifact(parent_source),
            "generated_scanner_source": artifact(generated_source),
            "scanner_binary": artifact(binary),
        },
        "donor_accounting": {
            "public_payload_bytes": DONOR_PAYLOAD_BYTES,
            "public_total_score_bytes": DONOR_TOTAL_SCORE_BYTES,
            "current_target_bytes": 105_000_000,
            "public_score_debt_bytes": DONOR_TOTAL_SCORE_BYTES - 105_000_000,
            "modeled_stream_bytes": EXPECTED_INPUT_BYTES,
            "direct_history_ring_bytes": 60_000_000,
        },
        "scan": scan,
        "ledger": {
            **validation,
            "compressed_bytes": len(compressed_a),
            "compression_ratio": len(compressed_a) / len(ledgers[0]),
        },
        "accounting": {
            "payload_rate_equivalent_gross_bytes": gross,
            "compressed_ledger_bytes": len(compressed_a),
            "frozen_integration_allowance_bytes": INTEGRATION_ALLOWANCE_BYTES,
            "payload_rate_equivalent_net_bytes": net,
            "proxy_total_score_bytes": DONOR_TOTAL_SCORE_BYTES - net,
            "promotion_floor_bytes": 4_500_000,
            "diagnostic_source_package_bytes": len(source_package),
            "score_credit_bytes": 0,
        },
        "proof": {
            "receipt_bound_modeled_stream": True,
            "scan_summary_deterministic": scans[0] == scans[1],
            "raw_ledger_deterministic": ledgers[0] == ledgers[1],
            "compressed_ledger_deterministic": compressed_a == compressed_b,
            "ledger_parse_valid": bool(validation["component_record_counts_equal"]),
            "prior_source_only": bool(scan["selected_sources_strictly_prior"]),
            "fully_closed_sources": bool(scan["selected_sources_fully_closed"]),
            "all_selected_anchors_exact": bool(scan["selected_anchors_exactly_verified"]),
        },
        "artifacts": {
            "raw_ledger": artifact(ledger_paths[0]),
            "compressed_ledger": artifact(compressed_path),
            "diagnostic_source_package": artifact(source_path),
        },
        "failed_conditions": failed,
        "claim_boundary": "Exact post-WRT copy/ledger ceiling on an external donor stream. Payload-rate accounting assumes copied bytes cost the donor average and does not measure residual interaction. No modified cmix archive, exact donor forecast, memory/runtime eligibility, or official score is claimed.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "copied_bytes": copied,
        "compressed_ledger_bytes": len(compressed_a),
        "net_proxy_bytes": net,
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
