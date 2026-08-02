#!/usr/bin/env python3
"""Run the frozen NNCP v3.3 CPU encode-only causal-speed Q0."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_cpu_encode_only_causal_speed_q0_v1"
LIMIT_KIB = 9_765_625
REFERENCE_SECONDS = 279.797
ELAPSED_CEILING = 139.8985
REFERENCE_ARCHIVE_BYTES = 9_246
REFERENCE_ARCHIVE_SHA256 = (
    "097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5"
)
BINARY_SHA256 = (
    "c3f6ee27f5ac69b58b3fc3d487d18fb2ef949f6eb197d6e709a972d80a65f34c"
)
LIBRARY_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
TRACE_MAGIC = b"NNTCHD2\0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def guarded_run(
    command: list[str], guard: Path, label: str, environment: dict[str, str]
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    guarded = [
        sys.executable,
        str((ROOT / "tools/run_with_rss_guard.py").resolve()),
        "--limit-kib",
        str(LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(LIMIT_KIB),
        "--sample-interval",
        "0.2",
        "--guard-json",
        str(guard.resolve()),
        "--label",
        label,
        "--",
        *command,
    ]
    completed = subprocess.run(
        guarded, check=False, capture_output=True, text=True, env=environment
    )
    if not guard.is_file():
        raise RuntimeError(f"RSS guard produced no receipt for {label}")
    receipt = json.loads(guard.read_text())
    if completed.returncode != 0 or receipt.get("status") != "complete":
        raise RuntimeError(
            f"guarded command failed for {label}: "
            f"returncode={completed.returncode} status={receipt.get('status')}"
        )
    return completed, receipt


def read_trace(path: Path) -> list[dict[str, object]]:
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != TRACE_MAGIC:
        raise ValueError("malformed NNCP teacher trace header")
    row_count = int.from_bytes(data[8:16], "little")
    offset = 16
    rows: list[dict[str, object]] = []
    for _ in range(row_count):
        if offset + 44 > len(data):
            raise ValueError("truncated NNCP teacher trace row")
        header = data[offset : offset + 44]
        offset += 44
        original_index = int.from_bytes(header[0:8], "little")
        execution_row = int.from_bytes(header[8:16], "little")
        local_position = int.from_bytes(header[32:36], "little")
        stream_index = int.from_bytes(header[36:38], "little")
        symbol = int.from_bytes(header[38:40], "little")
        symbol_count = int.from_bytes(header[40:44], "little")
        byte_count = 4 * symbol_count
        if symbol_count < 2 or offset + byte_count > len(data):
            raise ValueError("invalid NNCP teacher distribution length")
        raw = data[offset : offset + byte_count]
        offset += byte_count
        values = struct.unpack(f"<{symbol_count}f", raw)
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("nonfinite or negative NNCP probability")
        total = math.fsum(values)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"NNCP distribution total {total} is not normalized")
        rows.append(
            {
                "original_index": original_index,
                "execution_row": execution_row,
                "local_position": local_position,
                "stream_index": stream_index,
                "symbol": symbol,
                "symbol_count": symbol_count,
                "distribution": raw,
            }
        )
    if offset != len(data):
        raise ValueError("trailing bytes in NNCP teacher trace")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp"),
    )
    parser.add_argument(
        "--library",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so"
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_full_attribution_trace_1m_v1.restored"
        ),
    )
    parser.add_argument(
        "--reference-archive",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "nncp_teacher_trace_smoke_v1/trace_off.bin"
        ),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results" / CANDIDATE_ID
    )
    args = parser.parse_args()

    required = (args.binary, args.library, args.input, args.reference_archive)
    if not all(path.is_file() for path in required):
        raise SystemExit("missing NNCP binary, library, input, or reference archive")
    if sha256(args.binary) != BINARY_SHA256:
        raise ValueError("NNCP binary identity mismatch")
    if sha256(args.library) != LIBRARY_SHA256:
        raise ValueError("LibNC CPU library identity mismatch")
    if (
        args.reference_archive.stat().st_size != REFERENCE_ARCHIVE_BYTES
        or sha256(args.reference_archive) != REFERENCE_ARCHIVE_SHA256
    ):
        raise ValueError("T4 reference archive identity mismatch")
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite an encode-only Q0 decision")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    environment = dict(os.environ)
    environment.pop("NNCP_TEACHER_TRACE", None)
    environment.pop("NNCP_BRANCH_TRACE", None)
    speed_archives: list[dict[str, object]] = []
    speed_receipts: list[dict[str, object]] = []
    base_command = [
        str(args.binary.resolve()),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--encode_only",
        "--preprocess",
        "16384,512",
        "--max_size",
        "10000",
        "c",
        str(args.input.resolve()),
    ]

    first_archive = args.output_dir / "encode_only_a.bin"
    first_guard = args.output_dir / "speed_a_guard.json"
    _, first_receipt = guarded_run(
        [*base_command, str(first_archive.resolve())],
        first_guard,
        f"{CANDIDATE_ID}_speed_a",
        environment,
    )
    first_elapsed = float(first_receipt["elapsed_s"])
    first_memory_clean = (
        not first_receipt.get("rss_guard_exceeded", False)
        and int(first_receipt["max_sampled_tree_rss_kib"]) <= LIMIT_KIB
    )
    speed_pass = first_elapsed <= ELAPSED_CEILING and first_memory_clean
    speed_archives.append(
        {
            "path": str(first_archive),
            "bytes": first_archive.stat().st_size,
            "sha256": sha256(first_archive),
        }
    )
    speed_receipts.append(first_receipt)

    determinism_pass = False
    causality_pass = False
    observation_neutral = False
    probability_rows = 0
    causality_compared_rows = 0
    mini_artifacts: dict[str, object] = {}

    if speed_pass:
        second_archive = args.output_dir / "encode_only_b.bin"
        second_guard = args.output_dir / "speed_b_guard.json"
        _, second_receipt = guarded_run(
            [*base_command, str(second_archive.resolve())],
            second_guard,
            f"{CANDIDATE_ID}_speed_b",
            environment,
        )
        speed_archives.append(
            {
                "path": str(second_archive),
                "bytes": second_archive.stat().st_size,
                "sha256": sha256(second_archive),
            }
        )
        speed_receipts.append(second_receipt)
        determinism_pass = first_archive.read_bytes() == second_archive.read_bytes()

        with tempfile.TemporaryDirectory(prefix="nncp-encode-only-q0-") as temp_name:
            temp = Path(temp_name)
            input_a = temp / "a.raw"
            input_b = temp / "b.raw"
            data_a = bytes((index * 73 + 19) & 255 for index in range(2048))
            data_b = bytearray(data_a)
            data_b[32] ^= 0x5A
            input_a.write_bytes(data_a)
            input_b.write_bytes(data_b)
            mini_base = [
                str(args.binary.resolve()),
                "-q",
                "-T",
                "4",
                "--profile",
                "enwik9",
                "--encode_only",
                "--batch_size",
                "32",
                "--block_len",
                "2048",
                "--n_symb",
                "256",
                "--max_size",
                "2048",
                "c",
            ]
            archive_off = temp / "a_off.bin"
            subprocess.run(
                [*mini_base, str(input_a), str(archive_off)],
                check=True,
                capture_output=True,
                env=environment,
            )
            trace_a = args.output_dir / "causal_a.trace"
            archive_a = args.output_dir / "causal_a.bin"
            env_a = dict(environment)
            env_a["NNCP_TEACHER_TRACE"] = str(trace_a.resolve())
            subprocess.run(
                [*mini_base, str(input_a), str(archive_a)],
                check=True,
                capture_output=True,
                env=env_a,
            )
            trace_b = args.output_dir / "causal_b.trace"
            archive_b = args.output_dir / "causal_b.bin"
            env_b = dict(environment)
            env_b["NNCP_TEACHER_TRACE"] = str(trace_b.resolve())
            subprocess.run(
                [*mini_base, str(input_b), str(archive_b)],
                check=True,
                capture_output=True,
                env=env_b,
            )
            observation_neutral = archive_off.read_bytes() == archive_a.read_bytes()
            rows_a = read_trace(trace_a)
            rows_b = read_trace(trace_b)
            if len(rows_a) != len(rows_b):
                raise ValueError("causality trace row counts differ")
            probability_rows = len(rows_a) + len(rows_b)
            causality_pass = True
            for row_a, row_b in zip(rows_a, rows_b, strict=True):
                if (
                    row_a["stream_index"] == 0
                    and int(row_a["local_position"]) > 32
                ):
                    continue
                causality_compared_rows += 1
                if (
                    row_a["stream_index"] != row_b["stream_index"]
                    or row_a["local_position"] != row_b["local_position"]
                    or row_a["symbol_count"] != row_b["symbol_count"]
                    or row_a["distribution"] != row_b["distribution"]
                ):
                    causality_pass = False
                    break
            mini_artifacts = {
                "input_a_sha256": hashlib.sha256(data_a).hexdigest(),
                "input_b_sha256": hashlib.sha256(data_b).hexdigest(),
                "changed_raw_index": 32,
                "trace_a_sha256": sha256(trace_a),
                "trace_b_sha256": sha256(trace_b),
                "archive_trace_off_sha256": sha256(archive_off),
                "archive_trace_on_sha256": sha256(archive_a),
                "archive_perturbed_sha256": sha256(archive_b),
            }

    passed = (
        speed_pass
        and determinism_pass
        and causality_pass
        and observation_neutral
        and probability_rows > 0
    )
    result = {
        "schema": "gamma.nncp_v33_libnc_cpu_encode_only_causal_speed_q0.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Non-decodable encode-only teacher execution evidence only; no "
            "constructive codec, forecast, package, or full-corpus claim."
        ),
        "contract": {
            "profile": "enwik9",
            "threads": 4,
            "teacher_symbols": 10_000,
            "reference_elapsed_seconds": REFERENCE_SECONDS,
            "elapsed_ceiling_seconds": ELAPSED_CEILING,
            "required_elapsed_reduction_fraction": 0.5,
            "decimal_memory_limit_kib": LIMIT_KIB,
            "causality_control_symbols": 2_048,
            "causality_changed_stream": 0,
            "causality_changed_local_state": 32,
        },
        "inputs": {
            "script_sha256": sha256(Path(__file__).resolve()),
            "binary_sha256": sha256(args.binary),
            "library_sha256": sha256(args.library),
            "input_bytes": args.input.stat().st_size,
            "input_sha256": sha256(args.input),
            "reference_archive_bytes": REFERENCE_ARCHIVE_BYTES,
            "reference_archive_sha256": REFERENCE_ARCHIVE_SHA256,
        },
        "speed": {
            "command": base_command,
            "first_elapsed_seconds": first_elapsed,
            "elapsed_reduction_fraction": 1.0 - first_elapsed / REFERENCE_SECONDS,
            "first_memory_clean": first_memory_clean,
            "archives": speed_archives,
            "guard_receipts": speed_receipts,
            "pass": speed_pass,
        },
        "integrity": {
            "repeat_archive_byte_identical": determinism_pass,
            "observation_neutral_archive": observation_neutral,
            "causality_preceding_distributions_identical": causality_pass,
            "causality_compared_rows": causality_compared_rows,
            "legal_normalized_probability_rows": probability_rows,
            "mini_artifacts": mini_artifacts,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "run one continuous full-dictionary teacher to the 9M-10M window"
                if passed
                else "retire the exact CPU encode-only execution path unchanged"
            ),
            "forecast_bytes": 109_389_323,
            "design_target_bytes": 108_000_000,
            "forecast_debt_bytes": 1_389_323,
            "verified_full_1g_score_bytes": None,
        },
    }
    decision_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
