#!/usr/bin/env python3
"""Build and certify the exact native NNCP 32/32 update schedule."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_exact_midsegment32_qm2_v1"
SOURCE_TAR = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05.tar.gz")
PATCH = ROOT / "programs" / CANDIDATE_ID / "nncp_midsegment32.patch"
INPUT = Path(
    "/home/x/enwiki9-nonproof/results/"
    "fx2_full_attribution_trace_1m_v1.restored"
)
BASELINE = ROOT / "results/nncp_v33_cpu_t16_archive_identity_q0_v1/t16_archive.bin"
EXPECTED = {
    "source_tar": "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    "baseline": "097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5",
}
BASELINE_BYTES = 9_246
GAIN_GATE_BYTES = 500
MAX_SOURCE_PACKAGE_BYTES = 1_300_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": command,
        "elapsed_seconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def serialized_schedule_header(path: Path) -> dict[str, object]:
    header = path.read_bytes()[:19]
    if len(header) != 19:
        raise ValueError("candidate archive is shorter than the fixed header")
    magic, version = struct.unpack(">IH", header[:6])
    use_cuda = header[6]
    use_bf16 = header[7]
    batch_size, segment_length, vocabulary = struct.unpack(">HHH", header[8:14])
    seed = struct.unpack(">I", header[14:18])[0]
    midsegment32 = header[18]
    return {
        "magic": magic,
        "version": version,
        "use_cuda": use_cuda,
        "use_bf16": use_bf16,
        "batch_size": batch_size,
        "segment_length": segment_length,
        "vocabulary": vocabulary,
        "seed": seed,
        "midsegment32": midsegment32,
        "valid": (
            magic == 0xB727AC58
            and version == 2
            and batch_size == 32
            and segment_length == 64
            and midsegment32 == 1
        ),
    }


def main() -> int:
    inputs = {
        "source_tar": SOURCE_TAR,
        "patch": PATCH,
        "input": INPUT,
        "baseline": BASELINE,
    }
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    if sha256(SOURCE_TAR) != EXPECTED["source_tar"]:
        raise ValueError("NNCP source-tar identity mismatch")
    if BASELINE.stat().st_size != BASELINE_BYTES or sha256(BASELINE) != EXPECTED["baseline"]:
        raise ValueError("10,000-symbol faithful archive identity mismatch")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    archive_a = output_dir / "archive_a.nncp"
    archive_b = output_dir / "archive_b.nncp"
    restored = output_dir / "restored.raw"

    with tempfile.TemporaryDirectory(prefix="nncp-exact-midsegment32-") as tmp:
        build_root = Path(tmp)
        extract = run(
            ["tar", "-xzf", str(SOURCE_TAR), "-C", str(build_root)],
            cwd=build_root,
        )
        source_root = build_root / "nncp-2024-06-05"
        patch_run = run(
            ["patch", "-p1", "-i", str(PATCH)],
            cwd=source_root,
        )
        build = run(["make", "-j4"], cwd=source_root)
        binary = source_root / "nncp"
        library = source_root / "libnc.so"
        binary_identity = {
            "bytes": binary.stat().st_size,
            "sha256": sha256(binary),
        }
        library_identity = {
            "bytes": library.stat().st_size,
            "sha256": sha256(library),
        }
        environment = os.environ.copy()
        environment["LD_LIBRARY_PATH"] = str(source_root)
        common = [
            str(binary),
            "-q",
            "-T",
            "4",
            "--profile",
            "enwik9",
            "--midsegment32",
            "--preprocess",
            "16384,512",
            "--max_size",
            "10000",
            "c",
            str(INPUT),
        ]
        print(json.dumps({"event": "encode_a_start"}), flush=True)
        encode_a = run([*common, str(archive_a)], cwd=source_root, environment=environment)
        print(json.dumps({"archive_bytes": archive_a.stat().st_size, "event": "encode_a_complete"}), flush=True)
        print(json.dumps({"event": "encode_b_start"}), flush=True)
        encode_b = run([*common, str(archive_b)], cwd=source_root, environment=environment)
        print(json.dumps({"archive_bytes": archive_b.stat().st_size, "event": "encode_b_complete"}), flush=True)
        print(json.dumps({"event": "decode_start"}), flush=True)
        decode = run(
            [str(binary), "-q", "-T", "4", "d", str(archive_a), str(restored)],
            cwd=source_root,
            environment=environment,
        )

    archive_identity = archive_a.read_bytes() == archive_b.read_bytes()
    restored_bytes = restored.read_bytes()
    raw_prefix_identity = bool(restored_bytes) and INPUT.read_bytes().startswith(restored_bytes)
    schedule_header = serialized_schedule_header(archive_a)
    candidate_bytes = archive_a.stat().st_size
    actual_gain = BASELINE_BYTES - candidate_bytes
    compressed_patch_bytes = len(lzma.compress(PATCH.read_bytes(), preset=9))
    source_package_bytes = SOURCE_TAR.stat().st_size + compressed_patch_bytes
    failed: list[str] = []
    if not archive_identity:
        failed.append("repeated_archives_differ")
    if not raw_prefix_identity:
        failed.append("raw_prefix_decode_failed")
    if not schedule_header["valid"]:
        failed.append("serialized_schedule_header_invalid")
    if actual_gain < GAIN_GATE_BYTES:
        failed.append("actual_gain_below_500")
    if source_package_bytes > MAX_SOURCE_PACKAGE_BYTES:
        failed.append("source_package_above_1300000")
    promotion = not failed

    decision = {
        "schema": "enwiki9_nncp_libnc_exact_midsegment32_qm2_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_NATIVE_MATURITY" if promotion else "REJECT",
        "verdict": "authorize_exact_native_maturity_gate" if promotion else "retire_exact_native_midsegment32_realization",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact source-native 10,000-symbol schedule gate with two encodes, "
            "patched decode, serialized mode identity, and official NNCP raw "
            "inverse. It is not a full-corpus score and receives zero score credit."
        ),
        "configuration": {
            "profile": "enwik9",
            "threads": 4,
            "batch_size": 32,
            "segment_length": 64,
            "midpoint": 32,
            "updates_per_segment": 2,
            "first_half_future_inputs": "zero",
            "midpoint_memory_shift": False,
            "post_update_first_half_replay": True,
            "learning_rate_coordinate": "parent_segment",
            "preprocess": "16384,512",
            "max_symbols": 10_000,
        },
        "comparison": {
            "faithful_archive_bytes": BASELINE_BYTES,
            "faithful_archive_sha256": EXPECTED["baseline"],
            "candidate_archive_bytes": candidate_bytes,
            "candidate_archive_sha256": sha256(archive_a),
            "actual_gain_bytes": actual_gain,
            "required_actual_gain_bytes": GAIN_GATE_BYTES,
        },
        "integrity": {
            "archive_repeat_byte_identical": archive_identity,
            "raw_prefix_decode_exact": raw_prefix_identity,
            "restored_raw_bytes": len(restored_bytes),
            "restored_raw_sha256": sha256(restored),
            "serialized_schedule_header": schedule_header,
        },
        "program_accounting": {
            "source_tar_bytes": SOURCE_TAR.stat().st_size,
            "patch_bytes": PATCH.stat().st_size,
            "compressed_patch_bytes": compressed_patch_bytes,
            "complete_source_package_bytes": source_package_bytes,
            "maximum_source_package_bytes": MAX_SOURCE_PACKAGE_BYTES,
            "compiled_binary": binary_identity,
            "runtime_library": library_identity,
        },
        "execution": {
            "extract": extract,
            "patch": patch_run,
            "build": build,
            "encode_a": encode_a,
            "encode_b": encode_b,
            "decode": decode,
        },
        "inputs": {
            name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for name, path in inputs.items()
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
            "target_bytes": 105_000_000,
        },
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-libnc-exact-midsegment32-qm2: {error}", file=os.sys.stderr)
        raise
