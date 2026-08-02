#!/usr/bin/env python3
"""Run the frozen full-dictionary NNCP 9M-10M teacher headroom gate."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import tempfile

import numpy as np

from janus_paid_residual_mdl_oracle import range_decode, range_encode
from materialize_nncp_native_indexed_trace_observer import materialize
from radix_island_oracle import emission_groups
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_cpu_encode_only_mature_9m_10m_q1_v1"
LIMIT_KIB = 9_765_625
GROSS_GATE_BPM = 3_000.0
SMOKE_SYMBOLS = 10_000
P1_MAGIC = b"CMX21P1\0"
TRACE_MAGIC = b"NNNTR4\0\0"
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")
PROBABILITY_TOTAL = 32_768

EXPECTED = {
    "source_package": (
        1_180_969,
        "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    ),
    "original_binary": (
        496_760,
        "c3f6ee27f5ac69b58b3fc3d487d18fb2ef949f6eb197d6e709a972d80a65f34c",
    ),
    "original_library": (
        None,
        "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e",
    ),
    "dictionary": (
        186_264,
        "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1",
    ),
    "preprocessed": (
        401_217_922,
        "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    ),
    "symbol_map": (
        3_610_961_314,
        "b9e0c570fb12fe3baa35cc8d877a11735065ed56ce30c3fca68b74ce794c3085",
    ),
    "map_receipt": (
        2_941,
        "8de43815a6156096fd792a462831e90b0a5fca747b679d1e7f3a54671490e5b7",
    ),
    "window_manifest": (
        3_046,
        "487cf74aee57277f7a29929966284ba7e004768b86e0b98a0142fcf8b933aad1",
    ),
    "joint_p1": (
        100_029_648,
        "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719",
    ),
    "wrt_store": (
        6_251_857,
        "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b",
    ),
    "wrt_dictionary": (
        411_996,
        "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a",
    ),
    "raw_10m": (
        10_000_000,
        "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97",
    ),
    "q0_decision": (
        6_401,
        "f5349c724aa5752161bf7c47b796972dbc31b616d4baa74c567df1901dd4868d",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file(label: str, path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"missing {label}: {path}")
    expected_bytes, expected_sha256 = EXPECTED[label]
    actual_bytes = path.stat().st_size
    actual_sha256 = sha256(path)
    if expected_bytes is not None and actual_bytes != expected_bytes:
        raise ValueError(f"{label} byte identity mismatch")
    if actual_sha256 != expected_sha256:
        raise ValueError(f"{label} SHA-256 identity mismatch")
    return {
        "bytes": actual_bytes,
        "path": str(path),
        "sha256": actual_sha256,
    }


def expected_bits(symbol: int, vocabulary: int) -> list[int]:
    start = 0
    active = vocabulary
    bits: list[int] = []
    while active > 1:
        left = active >> 1
        bit = int(symbol >= start + left)
        bits.append(bit)
        if bit:
            start += left
            active -= left
        else:
            active = left
    if start != symbol:
        raise ValueError("branch path does not terminate at symbol")
    return bits


def verify_trace(
    path: Path,
    expected_symbols: np.memmap,
    expected_rows: int,
    selection_start: int,
    selection_end: int,
) -> tuple[dict[str, object], np.ndarray, np.ndarray]:
    selected_probabilities = array("H")
    selected_truth = bytearray()
    seen = np.zeros(expected_rows, dtype=np.uint8)
    selected_symbols = 0
    with path.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
        if len(header) != TRACE_HEADER.size:
            raise ValueError("truncated native trace header")
        magic, rows, branches, trees, checkpoint_rows = TRACE_HEADER.unpack(header)
        if magic != TRACE_MAGIC:
            raise ValueError("native trace magic mismatch")
        if trees != 0:
            raise ValueError("Q1 trace unexpectedly contains derived trees")
        observed_branches = 0
        checkpoints: list[dict[str, int]] = []
        prior_bits: int | None = None
        prior_bytes: int | None = None
        for index in range(rows):
            raw_row = source.read(TRACE_ROW.size)
            if len(raw_row) != TRACE_ROW.size:
                raise ValueError("truncated native trace row")
            (
                original_index,
                execution,
                before_bits,
                after_bits,
                before_bytes,
                after_bytes,
                exact_archive_bits,
                exact_archive_bytes,
                symbol,
                vocabulary,
                branch_count,
                has_tree,
                checkpoint,
            ) = TRACE_ROW.unpack(raw_row)
            if execution != index:
                raise ValueError("nonconsecutive native trace ordinal")
            if original_index >= expected_rows or seen[original_index]:
                raise ValueError("native original ordinal is invalid or duplicated")
            seen[original_index] = 1
            if vocabulary < 2 or symbol >= vocabulary:
                raise ValueError("invalid native symbol domain")
            if symbol != int(expected_symbols[original_index]):
                raise ValueError("native truth differs from frozen preprocessed input")
            if has_tree != 0 or checkpoint not in (0, 1):
                raise ValueError("invalid native trace flags")
            if after_bits < before_bits or after_bytes < before_bytes:
                raise ValueError("native range-coder count decreased")
            if prior_bits is not None and before_bits != prior_bits:
                raise ValueError("native bit count is discontinuous")
            if prior_bytes is not None and before_bytes != prior_bytes:
                raise ValueError("native byte count is discontinuous")
            bits = expected_bits(symbol, vocabulary)
            if len(bits) != branch_count:
                raise ValueError("native branch count mismatch")
            selected = selection_start <= original_index < selection_end
            if selected:
                selected_symbols += 1
            for expected_bit in bits:
                raw_branch = source.read(TRACE_BRANCH.size)
                if len(raw_branch) != TRACE_BRANCH.size:
                    raise ValueError("truncated native trace branch")
                probability, bit = TRACE_BRANCH.unpack(raw_branch)
                if bit != expected_bit:
                    raise ValueError("native branch truth mismatch")
                if not 1 <= probability < PROBABILITY_TOTAL:
                    raise ValueError("native branch probability is illegal")
                if selected:
                    selected_probabilities.append(probability)
                    selected_truth.append(bit)
            observed_branches += branch_count
            if checkpoint:
                if exact_archive_bits <= 0 or exact_archive_bytes <= 0:
                    raise ValueError("checkpoint lacks terminated archive count")
                checkpoints.append(
                    {
                        "completed_symbols": index + 1,
                        "exact_archive_bits": exact_archive_bits,
                        "exact_archive_bytes": exact_archive_bytes,
                    }
                )
            elif exact_archive_bits != 0 or exact_archive_bytes != 0:
                raise ValueError("non-checkpoint has terminated archive count")
            prior_bits = after_bits
            prior_bytes = after_bytes
        if source.read(1):
            raise ValueError("native trace has trailing bytes")
    if observed_branches != branches or len(checkpoints) != checkpoint_rows:
        raise ValueError("native trace header totals disagree")
    if rows != expected_rows or not np.all(seen):
        raise ValueError("native trace does not cover every original symbol once")
    if selected_symbols != selection_end - selection_start:
        raise ValueError("native trace selected-symbol coverage mismatch")
    metadata = {
        "bytes": path.stat().st_size,
        "checkpoints": checkpoints,
        "derived_tree_rows": trees,
        "original_ordinal_permutation_exact": True,
        "selected_branches": len(selected_truth),
        "selected_symbols": selected_symbols,
        "sha256": sha256(path),
        "symbol_rows": rows,
        "visited_branches": branches,
    }
    probabilities = np.frombuffer(
        selected_probabilities, dtype=np.uint16
    ).copy()
    truth = np.frombuffer(selected_truth, dtype=np.uint8).copy()
    return metadata, probabilities, truth


def run_command(
    command: list[str], environment: dict[str, str], stdout: Path, stderr: Path
) -> None:
    with stdout.open("w") as output, stderr.open("w") as errors:
        completed = subprocess.run(
            command,
            check=False,
            env=environment,
            stdout=output,
            stderr=errors,
            text=True,
        )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed with {completed.returncode}: {' '.join(command)}"
        )


def guarded_run(
    command: list[str], environment: dict[str, str], guard: Path, label: str
) -> dict[str, object]:
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
        "0.5",
        "--guard-json",
        str(guard.resolve()),
        "--label",
        label,
        "--",
        *command,
    ]
    completed = subprocess.run(guarded, check=False, env=environment)
    if not guard.is_file():
        raise RuntimeError("RSS guard produced no receipt")
    receipt = json.loads(guard.read_text())
    if completed.returncode != 0 or receipt.get("status") != "complete":
        raise RuntimeError(
            f"guarded execution failed: returncode={completed.returncode} "
            f"status={receipt.get('status')}"
        )
    if receipt.get("rss_guard_exceeded"):
        raise RuntimeError("decimal memory guard was exceeded")
    return receipt


def command_for(
    binary: Path,
    dictionary: Path,
    preprocessed: Path,
    symbols: int,
    archive: Path,
) -> list[str]:
    return [
        str(binary.resolve()),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--encode_only",
        "--dict",
        str(dictionary.resolve()),
        "--max_size",
        str(symbols),
        "c",
        str(preprocessed.resolve()),
        str(archive.resolve()),
    ]


def exact_joint_parent(
    joint_p1_path: Path,
    wrt_store: Path,
    wrt_dictionary: Path,
    raw_10m: Path,
    raw_start: int,
    raw_end: int,
    output_dir: Path,
) -> dict[str, object]:
    print(json.dumps({"stage": "joint_parent_boundaries"}), flush=True)
    parsed = parse_store(wrt_store, wrt_dictionary)
    if parsed.decoded != raw_10m.read_bytes():
        raise ValueError("official WRT inverse differs from the bound raw 10M")
    boundary_stream_bytes: dict[int, int] = {}
    for group in emission_groups(parsed):
        if group.raw_end in (raw_start, raw_end):
            boundary_stream_bytes[group.raw_end] = group.stream_end
    if set(boundary_stream_bytes) != {raw_start, raw_end}:
        raise ValueError("mature raw boundary is not an exact WRT group boundary")
    truth = np.unpackbits(
        np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big"
    )
    with joint_p1_path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid joint P1 header")
    (row_count,) = struct.unpack_from("<Q", header, 8)
    if row_count != len(truth):
        raise ValueError("joint P1 and WRT truth row counts differ")
    probabilities = np.memmap(
        joint_p1_path,
        mode="r",
        dtype="<u2",
        offset=16,
        shape=(row_count,),
    )
    if np.any(probabilities == 0):
        raise ValueError("joint P1 contains zero probability")
    start_row = boundary_stream_bytes[raw_start] * 8
    end_row = boundary_stream_bytes[raw_end] * 8
    selected_probabilities = probabilities[start_row:end_row]
    selected_truth = truth[start_row:end_row]
    payload = range_encode(selected_probabilities, selected_truth)
    if not np.array_equal(
        range_decode(payload, selected_probabilities), selected_truth
    ):
        raise ValueError("joint window payload failed arithmetic decode")
    path = output_dir / "joint_window.payload"
    path.write_bytes(payload)
    return {
        "archive_bytes": len(payload),
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "arithmetic_decode_exact": True,
        "end_row": end_row,
        "selected_rows": end_row - start_row,
        "start_row": start_row,
        "wrt_end_byte": boundary_stream_bytes[raw_end],
        "wrt_start_byte": boundary_stream_bytes[raw_start],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-package",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05.tar.gz"),
    )
    parser.add_argument(
        "--original-binary",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp"),
    )
    parser.add_argument(
        "--original-library",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so"),
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/dictionary.bin"
        ),
    )
    parser.add_argument(
        "--preprocessed",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin"
        ),
    )
    parser.add_argument(
        "--symbol-map",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/symbol_raw_map.bin"
        ),
    )
    parser.add_argument(
        "--map-receipt",
        type=Path,
        default=ROOT / "results/nncp_full_symbol_map_v1/map_receipt.json",
    )
    parser.add_argument(
        "--window-manifest",
        type=Path,
        default=ROOT / "results/nncp_full_symbol_map_v1/window_manifest.json",
    )
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--wrt-dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument(
        "--raw-10m",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/gamma/projects/enwiki9/data/enwik9_10000000.bin"
        ),
    )
    parser.add_argument(
        "--q0-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_cpu_encode_only_causal_speed_q0_v1/decision.json",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results" / CANDIDATE_ID
    )
    args = parser.parse_args()

    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite a mature Q1 decision")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "source_package": args.source_package,
        "original_binary": args.original_binary,
        "original_library": args.original_library,
        "dictionary": args.dictionary,
        "preprocessed": args.preprocessed,
        "symbol_map": args.symbol_map,
        "map_receipt": args.map_receipt,
        "window_manifest": args.window_manifest,
        "joint_p1": args.joint_p1,
        "wrt_store": args.wrt_store,
        "wrt_dictionary": args.wrt_dictionary,
        "raw_10m": args.raw_10m,
        "q0_decision": args.q0_decision,
    }
    print(json.dumps({"stage": "input_identity"}), flush=True)
    inputs = {label: verify_file(label, path) for label, path in paths.items()}

    q0 = json.loads(args.q0_decision.read_text())
    if q0.get("status") != "PASS" or not q0.get("decision", {}).get(
        "promotion_authorized"
    ):
        raise ValueError("encode-only Q0 did not authorize mature Q1")
    manifest = json.loads(args.window_manifest.read_text())
    windows = {
        row["window_id"]: row for row in manifest.get("windows", [])
    }
    window = windows.get("mature_9m_10m")
    if window is None:
        raise ValueError("frozen mature window is absent")
    expected_window = {
        "raw_start": 9_000_000,
        "raw_end": 9_999_992,
        "symbol_start": 2_000_597,
        "symbol_end": 2_229_154,
    }
    for key, expected in expected_window.items():
        if int(window[key]) != expected:
            raise ValueError(f"frozen mature window {key} changed")
    expected_symbols = np.memmap(
        args.preprocessed,
        mode="r",
        dtype=">u2",
        shape=(expected_window["symbol_end"],),
    )

    joint = exact_joint_parent(
        args.joint_p1,
        args.wrt_store,
        args.wrt_dictionary,
        args.raw_10m,
        expected_window["raw_start"],
        expected_window["raw_end"],
        args.output_dir,
    )

    with tempfile.TemporaryDirectory(prefix="nncp-mature-q1-") as temp_name:
        workspace = Path(temp_name)
        with tarfile.open(args.source_package, "r:*") as archive:
            archive.extractall(workspace, filter="data")
        roots = [path for path in workspace.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise ValueError("unexpected NNCP source package layout")
        source_root = roots[0]
        patch_path = args.output_dir / "nncp_native_trace.patch"
        materialize(source_root, patch_path)
        print(json.dumps({"stage": "build_observer"}), flush=True)
        build = subprocess.run(
            ["make", "-C", str(source_root), "-j2"],
            check=False,
            text=True,
            capture_output=True,
        )
        (args.output_dir / "build.stdout").write_text(build.stdout)
        (args.output_dir / "build.stderr").write_text(build.stderr)
        if build.returncode != 0:
            raise RuntimeError("NNCP observer build failed")
        binary = source_root / "nncp"
        library = source_root / "libnc.so"

        original_environment = dict(os.environ)
        original_environment["LD_LIBRARY_PATH"] = str(args.original_binary.parent)
        patched_environment = dict(os.environ)
        patched_environment["LD_LIBRARY_PATH"] = str(source_root)
        for variable in (
            "NNCP_NATIVE_TRACE",
            "NNCP_NATIVE_TRACE_FULL_WINDOWS",
            "NNCP_NATIVE_TRACE_CHECKPOINTS",
        ):
            original_environment.pop(variable, None)
            patched_environment.pop(variable, None)

        print(json.dumps({"stage": "observer_neutrality_smoke"}), flush=True)
        original_smoke = args.output_dir / "smoke_original.nncp"
        patched_off_smoke = args.output_dir / "smoke_patched_off.nncp"
        patched_on_smoke = args.output_dir / "smoke_patched_on.nncp"
        smoke_trace_path = args.output_dir / "smoke_native_trace.bin"
        run_command(
            command_for(
                args.original_binary,
                args.dictionary,
                args.preprocessed,
                SMOKE_SYMBOLS,
                original_smoke,
            ),
            original_environment,
            args.output_dir / "smoke_original.stdout",
            args.output_dir / "smoke_original.stderr",
        )
        run_command(
            command_for(
                binary,
                args.dictionary,
                args.preprocessed,
                SMOKE_SYMBOLS,
                patched_off_smoke,
            ),
            patched_environment,
            args.output_dir / "smoke_patched_off.stdout",
            args.output_dir / "smoke_patched_off.stderr",
        )
        smoke_environment = dict(patched_environment)
        smoke_environment["NNCP_NATIVE_TRACE"] = str(smoke_trace_path.resolve())
        run_command(
            command_for(
                binary,
                args.dictionary,
                args.preprocessed,
                SMOKE_SYMBOLS,
                patched_on_smoke,
            ),
            smoke_environment,
            args.output_dir / "smoke_patched_on.stdout",
            args.output_dir / "smoke_patched_on.stderr",
        )
        smoke_bytes = original_smoke.read_bytes()
        if (
            patched_off_smoke.read_bytes() != smoke_bytes
            or patched_on_smoke.read_bytes() != smoke_bytes
        ):
            raise ValueError("native observer changed the smoke archive")
        smoke_trace, smoke_probabilities, smoke_truth = verify_trace(
            smoke_trace_path,
            expected_symbols,
            SMOKE_SYMBOLS,
            0,
            SMOKE_SYMBOLS,
        )
        smoke_payload = range_encode(smoke_probabilities, smoke_truth)
        if not np.array_equal(
            range_decode(smoke_payload, smoke_probabilities), smoke_truth
        ):
            raise ValueError("smoke subset arithmetic stream failed decode")

        long_archive = args.output_dir / "teacher_through_9m_10m.nncp"
        long_trace_path = args.output_dir / "teacher_native_trace.bin"
        long_guard = args.output_dir / "teacher_guard.json"
        long_command = command_for(
            binary,
            args.dictionary,
            args.preprocessed,
            expected_window["symbol_end"],
            long_archive,
        )
        long_environment = dict(patched_environment)
        long_environment["NNCP_NATIVE_TRACE"] = str(long_trace_path.resolve())
        if long_archive.exists() or long_trace_path.exists() or long_guard.exists():
            if not (long_archive.is_file() and long_trace_path.is_file() and long_guard.is_file()):
                raise RuntimeError("partial mature teacher artifacts require audit")
            guard_receipt = json.loads(long_guard.read_text())
            if guard_receipt.get("status") != "complete":
                raise RuntimeError("existing mature teacher guard is not complete")
            print(json.dumps({"stage": "reuse_completed_long_execution"}), flush=True)
        else:
            print(
                json.dumps(
                    {
                        "stage": "continuous_mature_teacher",
                        "max_symbols": expected_window["symbol_end"],
                    }
                ),
                flush=True,
            )
            guard_receipt = guarded_run(
                long_command,
                long_environment,
                long_guard,
                f"{CANDIDATE_ID}_continuous_teacher",
            )

        print(json.dumps({"stage": "verify_mature_trace"}), flush=True)
        teacher_trace, teacher_probabilities, teacher_truth = verify_trace(
            long_trace_path,
            expected_symbols,
            expected_window["symbol_end"],
            expected_window["symbol_start"],
            expected_window["symbol_end"],
        )
        teacher_payload = range_encode(teacher_probabilities, teacher_truth)
        if not np.array_equal(
            range_decode(teacher_payload, teacher_probabilities), teacher_truth
        ):
            raise ValueError("teacher window payload failed arithmetic decode")
        teacher_payload_path = args.output_dir / "teacher_window.payload"
        teacher_payload_path.write_bytes(teacher_payload)
        teacher_archive_bytes = len(teacher_payload)
        if teacher_archive_bytes <= 0:
            raise ValueError("mature teacher window archive is empty")
        memory_clean = (
            not guard_receipt.get("rss_guard_exceeded", False)
            and int(guard_receipt["max_sampled_tree_rss_kib"]) <= LIMIT_KIB
        )
        if not memory_clean:
            raise RuntimeError("mature teacher exceeded the decimal memory limit")
        build_receipt = {
            "binary": {
                "bytes": binary.stat().st_size,
                "sha256": sha256(binary),
            },
            "compiler": subprocess.run(
                ["gcc", "--version"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.splitlines()[0],
            "library": {
                "bytes": library.stat().st_size,
                "sha256": sha256(library),
            },
            "patch": {
                "bytes": patch_path.stat().st_size,
                "sha256": sha256(patch_path),
            },
        }

    raw_bytes = expected_window["raw_end"] - expected_window["raw_start"]
    joint_archive_bytes = int(joint["archive_bytes"])
    gain_bytes = joint_archive_bytes - teacher_archive_bytes
    gain_bpm = gain_bytes * 1_000_000.0 / raw_bytes
    promotion = gain_bpm >= GROSS_GATE_BPM
    decision = {
        "schema": "gamma.nncp_v33_libnc_cpu_encode_only_mature_9m_10m_q1.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_49M_50M_CONTINUATION" if promotion else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Non-decodable continuous causal teacher headroom only; no "
            "constructive codec, package, forecast, or full-corpus claim."
        ),
        "population": {
            **expected_window,
            "raw_bytes": raw_bytes,
            "continuous_from_symbol": 0,
            "window_id": "mature_9m_10m",
        },
        "parent": joint,
        "teacher": {
            "continuous_encode_only_archive": {
                "bytes": long_archive.stat().st_size,
                "sha256": sha256(long_archive),
            },
            "guard": guard_receipt,
            "trace": teacher_trace,
            "window_archive": {
                "arithmetic_decode_exact": True,
                "bytes": teacher_archive_bytes,
                "selected_branches": len(teacher_truth),
                "sha256": hashlib.sha256(teacher_payload).hexdigest(),
            },
        },
        "economics": {
            "gross_gain_bytes": gain_bytes,
            "gross_gain_bytes_per_raw_million": gain_bpm,
            "required_bytes_per_raw_million": GROSS_GATE_BPM,
        },
        "integrity": {
            "all_consumed_probabilities_legal_nonzero": True,
            "continuous_teacher_from_symbol_zero": True,
            "decimal_10gb_process_tree_pass": True,
            "joint_window_arithmetic_decode": True,
            "joint_raw_boundaries_exact": True,
            "native_original_ordinal_permutation_exact": True,
            "observer_smoke_archive_identity": True,
            "q0_causality_authorization": True,
            "teacher_window_arithmetic_decode": True,
        },
        "smoke": {
            "archive_bytes": len(smoke_bytes),
            "archive_sha256": hashlib.sha256(smoke_bytes).hexdigest(),
            "subset_archive_bytes": len(smoke_payload),
            "subset_archive_sha256": hashlib.sha256(smoke_payload).hexdigest(),
            "symbols": SMOKE_SYMBOLS,
            "trace": smoke_trace,
        },
        "build": build_receipt,
        "inputs": inputs,
        "decision": {
            "forecast_bytes": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "next_action": (
                "run the frozen continuous 49M-50M teacher continuation"
                if promotion
                else "retire this full-dictionary LibNC CPU mature-teacher lane"
            ),
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
        },
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
