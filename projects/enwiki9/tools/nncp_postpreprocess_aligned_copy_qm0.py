#!/usr/bin/env python3
"""Price aligned exact copies beyond NNCP enwik9's direct receptive field."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_postpreprocess_aligned_copy_qm0_v1"
EXPECTED_INPUT_BYTES = 401_217_922
EXPECTED_INPUT_SHA256 = "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5"
PUBLISHED_ARCHIVE_BYTES = 106_632_363
PUBLISHED_PROGRAM_BYTES = 628_955
PUBLISHED_TOTAL_BYTES = PUBLISHED_ARCHIVE_BYTES + PUBLISHED_PROGRAM_BYTES
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


def decode_ulebs(payload: bytes, expected: int) -> list[int]:
    values: list[int] = []
    value = 0
    shift = 0
    for byte in payload:
        value |= (byte & 127) << shift
        if byte & 128:
            shift += 7
            if shift > 63:
                raise ValueError("ULEB128 exceeds uint64")
        else:
            values.append(value)
            value = 0
            shift = 0
    if shift or len(values) != expected:
        raise ValueError("invalid ULEB128 column")
    return values


def validate_ledger(payload: bytes, expected_records: int) -> dict[str, int | bool]:
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("bad aligned ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != expected_records:
        raise ValueError("ledger record count differs from scan")
    if 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("ledger columns do not cover payload")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    gaps = decode_ulebs(payload[40:gap_end], records)
    distances = decode_ulebs(payload[gap_end:distance_end], records)
    lengths = decode_ulebs(payload[distance_end:], records)
    position = 0
    in_bounds = True
    for gap, distance, length in zip(gaps, distances, lengths, strict=True):
        target = position + gap
        if distance <= 0 or distance > target or length > distance or target + length > EXPECTED_INPUT_BYTES:
            in_bounds = False
            break
        position = target + length
    return {
        "records": records,
        "raw_bytes": len(payload),
        "gap_stream_bytes": gap_size,
        "distance_stream_bytes": distance_size,
        "length_stream_bytes": length_size,
        "all_fields_u16_aligned": all(
            value % 2 == 0 for column in (gaps, distances, lengths) for value in column
        ),
        "all_commands_prior_closed_and_in_bounds": in_bounds,
    }


def generated_scanner(parent_source: str) -> str:
    replacements = {
        "constexpr uint64_t kExpectedSize = 1000000000ULL;":
            "constexpr uint64_t kExpectedSize = 401217922ULL;",
        "constexpr uint64_t kMinimumDistance = 100000000ULL;":
            "constexpr uint64_t kMinimumDistance = 640ULL;",
        "constexpr uint64_t kArchiveOnlyForecast = 109128198ULL;":
            "constexpr uint64_t kArchiveOnlyForecast = 106632363ULL;",
        "if ((hash1 & kAnchorMask) == 0) {":
            "if ((position & 1) == 0 && (hash1 & kAnchorMask) == 0) {",
        """while (target > last_target_end && source > 0 &&
                     data[target - 1] == data[source - 1]) {
                --target;
                --source;
              }""":
            """while (target >= last_target_end + 2 && source >= 2 &&
                     data[target - 2] == data[source - 2] &&
                     data[target - 1] == data[source - 1]) {
                target -= 2;
                source -= 2;
              }""",
        """while (length < closed_length &&
                     data[target + length] == data[source + length]) {
                ++length;
              }""":
            """while (length + 2 <= closed_length &&
                     data[target + length] == data[source + length] &&
                     data[target + length + 1] == data[source + length + 1]) {
                length += 2;
              }""",
    }
    generated = parent_source
    for old, new in replacements.items():
        if generated.count(old) != 1:
            raise ValueError(f"aligned scanner replacement contract failed: {old[:80]}")
        generated = generated.replace(old, new)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/results/")
        / "nncp_full_symbol_map_v1_retry2/preprocessed.bin",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if args.input.stat().st_size != EXPECTED_INPUT_BYTES:
        raise ValueError("NNCP preprocessed input has wrong size")
    if sha256_file(args.input) != EXPECTED_INPUT_SHA256:
        raise ValueError("NNCP preprocessed input has wrong SHA-256")

    parent_source = ROOT / "tools/far_history_cdc_collective_ledger_qm1.cpp"
    generated_source = args.output_dir / "nncp_postpreprocess_aligned_copy_qm0.cpp"
    generated_source.write_text(generated_scanner(parent_source.read_text()))
    binary = args.output_dir / "nncp_postpreprocess_aligned_copy_qm0"
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
            raise RuntimeError(f"aligned scanner {suffix} failed with status {completed.returncode}")
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
        ROOT / "docs/nncp_postpreprocess_aligned_copy_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)

    gross = float(scan["average_rate_equivalent_gross_bytes"])
    net = gross - len(compressed_a) - INTEGRATION_ALLOWANCE_BYTES
    copied = int(scan["copied_bytes"])
    failed: list[str] = []
    if copied < 40_000_000:
        failed.append("copied_bytes_below_40000000")
    if net < 4_000_000:
        failed.append("archive_rate_net_below_4000000")
    if any(int(value) <= 0 for value in scan["split_copied_bytes"]):
        failed.append("stream_third_without_selected_copy")
    if scans[0] != scans[1]:
        failed.append("repeat_scan_summary_mismatch")
    if ledgers[0] != ledgers[1]:
        failed.append("repeat_raw_ledger_mismatch")
    if compressed_a != compressed_b:
        failed.append("repeat_compressed_ledger_mismatch")
    if not bool(validation["all_fields_u16_aligned"]):
        failed.append("ledger_field_not_u16_aligned")
    if not bool(validation["all_commands_prior_closed_and_in_bounds"]):
        failed.append("ledger_command_invalid")
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
        "schema": "enwiki9_nncp_postpreprocess_aligned_copy_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "external_parent_postpreprocess_representation_ceiling_zero_credit",
        "verdict": "authorize_native_nncp_residual_integration" if not failed else "retire_nncp_aligned_copy",
        "inputs": {
            "preprocessed_symbols": artifact(args.input),
            "full_symbol_map_decision": artifact(ROOT / "results/nncp_full_symbol_map_v1/decision.json"),
            "full_symbol_map_receipt": artifact(ROOT / "results/nncp_full_symbol_map_v1/map_receipt.json"),
            "parent_scanner_source": artifact(parent_source),
            "generated_scanner_source": artifact(generated_source),
            "scanner_binary": artifact(binary),
        },
        "nncp_accounting": {
            "published_archive_bytes": PUBLISHED_ARCHIVE_BYTES,
            "published_program_bytes": PUBLISHED_PROGRAM_BYTES,
            "published_total_score_bytes": PUBLISHED_TOTAL_BYTES,
            "current_target_bytes": 105_000_000,
            "published_score_debt_bytes": PUBLISHED_TOTAL_BYTES - 105_000_000,
            "preprocessed_stream_bytes": EXPECTED_INPUT_BYTES,
            "preprocessed_symbols": EXPECTED_INPUT_BYTES // 2,
            "direct_receptive_field_symbols": 320,
            "minimum_copy_distance_bytes": 640,
        },
        "scan": scan,
        "ledger": {
            **validation,
            "compressed_bytes": len(compressed_a),
            "compression_ratio": len(compressed_a) / len(ledgers[0]),
        },
        "accounting": {
            "archive_rate_equivalent_gross_bytes": gross,
            "compressed_ledger_bytes": len(compressed_a),
            "frozen_integration_allowance_bytes": INTEGRATION_ALLOWANCE_BYTES,
            "archive_rate_equivalent_net_bytes": net,
            "proxy_total_score_bytes": PUBLISHED_TOTAL_BYTES - net,
            "promotion_floor_bytes": 4_000_000,
            "diagnostic_source_package_bytes": len(source_package),
            "score_credit_bytes": 0,
        },
        "proof": {
            "receipt_bound_preprocessed_stream": True,
            "u16_alignment_preserved": bool(validation["all_fields_u16_aligned"]),
            "scan_summary_deterministic": scans[0] == scans[1],
            "raw_ledger_deterministic": ledgers[0] == ledgers[1],
            "compressed_ledger_deterministic": compressed_a == compressed_b,
            "prior_closed_in_bounds_commands": bool(validation["all_commands_prior_closed_and_in_bounds"]),
            "all_selected_anchors_exact": bool(scan["selected_anchors_exactly_verified"]),
        },
        "artifacts": {
            "raw_ledger": artifact(ledger_paths[0]),
            "compressed_ledger": artifact(compressed_path),
            "diagnostic_source_package": artifact(source_path),
        },
        "failed_conditions": failed,
        "claim_boundary": "Exact aligned copy/ledger ceiling on the published NNCP preprocessed alphabet. Archive-rate accounting assumes copied symbols cost the published average and does not measure changed neural training or residual interaction. Published CUDA score remains external; no native archive, eligibility, forecast, or score is claimed.",
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
