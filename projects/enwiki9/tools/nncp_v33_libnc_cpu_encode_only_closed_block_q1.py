#!/usr/bin/env python3
"""Run the frozen causally closed NNCP native-block teacher gate."""

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

import nncp_v33_libnc_cpu_encode_only_mature_9m_10m_q1 as legacy
from janus_paid_residual_mdl_oracle import range_decode, range_encode
from materialize_nncp_native_indexed_trace_observer import materialize


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CANDIDATE_ID = "nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1"
LIMIT_KIB = 9_765_625
GROSS_GATE_BPM = 3_000.0
SMOKE_SYMBOLS = 10_000
VOCABULARY = 16_392
PROBABILITY_TOTAL = 32_768
N_STREAMS = 32
SEGMENT_LENGTH = 64
NOMINAL_BLOCK_SYMBOLS = 500_000
BLOCK_SYMBOLS = (NOMINAL_BLOCK_SYMBOLS // (N_STREAMS * SEGMENT_LENGTH)) * (
    N_STREAMS * SEGMENT_LENGTH
)
SELECTION_START = 1_499_136
SELECTION_END = 1_998_848
EXECUTION_SYMBOLS = SELECTION_END
RAW_START = 6_757_802
RAW_END = 8_991_577
WRT_START = 4_182_331
WRT_END = 5_618_556
RAW_1G_BYTES = 1_000_000_000
RAW_1G_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
MAP_MAGIC = b"NNSMAP1\0"
MAP_HEADER_BYTES = 16
MAP_DTYPE = np.dtype(
    [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
)

BOUND_SOURCES = (
    "projects/enwiki9/docs/nncp_v33_libnc_cpu_encode_only_closed_block_q1_plan.md",
    "projects/enwiki9/tools/nncp_v33_libnc_cpu_encode_only_closed_block_q1.py",
    "projects/enwiki9/tools/nncp_v33_libnc_cpu_encode_only_mature_9m_10m_q1.py",
    "projects/enwiki9/tools/materialize_nncp_native_indexed_trace_observer.py",
    "projects/enwiki9/tools/materialize_nncp_native_trace_observer.py",
    "projects/enwiki9/tools/janus_paid_residual_mdl_oracle.py",
    "projects/enwiki9/tools/radix_island_oracle.py",
    "projects/enwiki9/tools/wrt_exact.py",
)

OBSERVER_ENVIRONMENT = (
    "NNCP_TEACHER_TRACE",
    "NNCP_BRANCH_TRACE",
    "NNCP_SAVE_COEFS",
    "NNCP_NATIVE_TRACE",
    "NNCP_NATIVE_TRACE_FULL_WINDOWS",
    "NNCP_NATIVE_TRACE_CHECKPOINTS",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
)


def sha256_prefix(path: Path, size: int) -> str:
    digest = hashlib.sha256()
    remaining = size
    with path.open("rb") as source:
        while remaining:
            block = source.read(min(8 << 20, remaining))
            if not block:
                raise ValueError("source ended before requested hash prefix")
            digest.update(block)
            remaining -= len(block)
    return digest.hexdigest()


def verify_raw_1g(path: Path, raw_10m: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size != RAW_1G_BYTES:
        raise ValueError("receipt-bound raw 1G artifact is missing or mis-sized")
    full_sha256 = legacy.sha256(path)
    if full_sha256 != RAW_1G_SHA256:
        raise ValueError("raw 1G SHA-256 identity mismatch")
    prefix_sha256 = sha256_prefix(path, 10_000_000)
    raw_10m_sha256 = legacy.sha256(raw_10m)
    if prefix_sha256 != raw_10m_sha256:
        raise ValueError("local raw 10M is not the receipt-bound raw 1G prefix")
    return {
        "bytes": path.stat().st_size,
        "path": str(path),
        "prefix_10m_sha256": prefix_sha256,
        "sha256": full_sha256,
    }


def bind_tracked_sources() -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    bindings: dict[str, object] = {}
    for relative in BOUND_SOURCES:
        worktree = REPO_ROOT / relative
        if not worktree.is_file():
            raise FileNotFoundError(f"missing bound source: {relative}")
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        current = worktree.read_bytes()
        if current != committed:
            raise ValueError(f"bound source differs from HEAD: {relative}")
        bindings[relative] = {
            "bytes": len(current),
            "sha256": hashlib.sha256(current).hexdigest(),
        }
    return {"git_commit": commit, "tracked_files": bindings}


def clean_environment(source: dict[str, str]) -> dict[str, str]:
    environment = dict(source)
    for variable in OBSERVER_ENVIRONMENT:
        environment.pop(variable, None)
    return environment


def verify_symbol_population(
    symbol_map: Path, preprocessed: Path
) -> dict[str, object]:
    if preprocessed.stat().st_size % 2:
        raise ValueError("preprocessed symbol stream is not 16-bit aligned")
    rows = preprocessed.stat().st_size // 2
    with symbol_map.open("rb") as source:
        header = source.read(MAP_HEADER_BYTES)
    if len(header) != MAP_HEADER_BYTES or header[:8] != MAP_MAGIC:
        raise ValueError("invalid symbol-map header")
    header_rows = int.from_bytes(header[8:16], "little")
    if header_rows != rows:
        raise ValueError("symbol-map and preprocessed row counts differ")
    if symbol_map.stat().st_size != MAP_HEADER_BYTES + rows * MAP_DTYPE.itemsize:
        raise ValueError("symbol-map byte size is inconsistent")
    mapping = np.memmap(
        symbol_map,
        mode="r",
        dtype=MAP_DTYPE,
        offset=MAP_HEADER_BYTES,
        shape=(rows,),
    )
    symbols = np.memmap(preprocessed, mode="r", dtype=">u2", shape=(rows,))
    checks = {
        "selection_start_raw": int(mapping[SELECTION_START]["raw_start"]),
        "selection_start_previous_raw_end": int(
            mapping[SELECTION_START - 1]["raw_end"]
        ),
        "selection_end_raw": int(mapping[SELECTION_END]["raw_start"]),
        "selection_end_previous_raw_end": int(
            mapping[SELECTION_END - 1]["raw_end"]
        ),
    }
    if set(checks.values()) != {RAW_START, RAW_END} or not (
        checks["selection_start_raw"]
        == checks["selection_start_previous_raw_end"]
        == RAW_START
        and checks["selection_end_raw"]
        == checks["selection_end_previous_raw_end"]
        == RAW_END
    ):
        raise ValueError("frozen complete-block raw boundaries changed")
    if not np.array_equal(
        mapping[SELECTION_START:SELECTION_END]["symbol"],
        symbols[SELECTION_START:SELECTION_END],
    ):
        raise ValueError("selected symbol-map values differ from prepared input")
    return {
        "block_symbols": SELECTION_END - SELECTION_START,
        "complete_block": True,
        "execution_symbols": EXECUTION_SYMBOLS,
        "map_rows": rows,
        "raw_end": RAW_END,
        "raw_start": RAW_START,
        "selected_symbols_match_preprocessed": True,
        **checks,
    }


def convert_prob0_to_p1(prob0: int) -> int:
    if not 1 <= prob0 < PROBABILITY_TOTAL:
        raise ValueError("native prob0 is outside the legal domain")
    p1 = 2 * (PROBABILITY_TOTAL - int(prob0))
    if not 2 <= p1 <= 65_534 or p1 % 2:
        raise ValueError("converted Q16 p1 is outside the legal domain")
    return p1


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
        header = source.read(legacy.TRACE_HEADER.size)
        if len(header) != legacy.TRACE_HEADER.size:
            raise ValueError("truncated native trace header")
        magic, rows, branches, trees, checkpoint_rows = legacy.TRACE_HEADER.unpack(
            header
        )
        if magic != legacy.TRACE_MAGIC or trees != 0:
            raise ValueError("native trace header or derived-tree count is invalid")
        observed_branches = 0
        observed_checkpoints = 0
        prior_bits: int | None = None
        prior_bytes: int | None = None
        for index in range(rows):
            raw_row = source.read(legacy.TRACE_ROW.size)
            if len(raw_row) != legacy.TRACE_ROW.size:
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
            ) = legacy.TRACE_ROW.unpack(raw_row)
            if execution != index:
                raise ValueError("native execution ordinal is not consecutive")
            if original_index >= expected_rows or seen[original_index]:
                raise ValueError("native original ordinal is invalid or duplicated")
            seen[original_index] = 1
            if vocabulary != VOCABULARY or symbol >= vocabulary:
                raise ValueError("native trace vocabulary or symbol is invalid")
            if symbol != int(expected_symbols[original_index]):
                raise ValueError("native truth differs from frozen prepared input")
            if has_tree != 0 or checkpoint not in (0, 1):
                raise ValueError("native trace flags are invalid")
            if after_bits < before_bits or after_bytes < before_bytes:
                raise ValueError("native range-coder count decreased")
            if prior_bits is not None and before_bits != prior_bits:
                raise ValueError("native bit count is discontinuous")
            if prior_bytes is not None and before_bytes != prior_bytes:
                raise ValueError("native byte count is discontinuous")
            bits = legacy.expected_bits(symbol, vocabulary)
            if len(bits) != branch_count:
                raise ValueError("native branch count differs from truth path")
            selected = selection_start <= original_index < selection_end
            if selected != (selection_start <= index < selection_end):
                raise ValueError("selected complete block is not execution-order closed")
            if selected:
                selected_symbols += 1
            for expected_bit in bits:
                raw_branch = source.read(legacy.TRACE_BRANCH.size)
                if len(raw_branch) != legacy.TRACE_BRANCH.size:
                    raise ValueError("truncated native trace branch")
                prob0, bit = legacy.TRACE_BRANCH.unpack(raw_branch)
                if bit != expected_bit:
                    raise ValueError("native branch truth mismatch")
                p1 = convert_prob0_to_p1(prob0)
                if selected:
                    selected_probabilities.append(p1)
                    selected_truth.append(bit)
            observed_branches += branch_count
            if checkpoint:
                observed_checkpoints += 1
                if exact_archive_bits <= 0 or exact_archive_bytes <= 0:
                    raise ValueError("checkpoint lacks terminated archive count")
            elif exact_archive_bits != 0 or exact_archive_bytes != 0:
                raise ValueError("non-checkpoint contains terminated archive count")
            prior_bits = after_bits
            prior_bytes = after_bytes
        if source.read(1):
            raise ValueError("native trace contains trailing bytes")
    if rows != expected_rows or observed_branches != branches:
        raise ValueError("native trace header totals disagree")
    if observed_checkpoints != checkpoint_rows:
        raise ValueError("native checkpoint total disagrees")
    if not np.all(seen):
        raise ValueError("native trace is not an exact original-ordinal permutation")
    if selected_symbols != selection_end - selection_start:
        raise ValueError("selected complete-block coverage differs")
    probabilities = np.frombuffer(selected_probabilities, dtype=np.uint16).copy()
    truth = np.frombuffer(selected_truth, dtype=np.uint8).copy()
    if len(probabilities) != len(truth):
        raise ValueError("teacher probability/truth lengths differ")
    if len(probabilities) and (
        int(probabilities.min()) < 2
        or int(probabilities.max()) > 65_534
        or np.any(probabilities % 2)
    ):
        raise ValueError("converted teacher p1 stream is illegal")
    metadata = {
        "bytes": path.stat().st_size,
        "checkpoint_rows": observed_checkpoints,
        "complete_block_execution_order_exact": True,
        "converted_p1_domain": [2, 65_534],
        "derived_tree_rows": trees,
        "original_ordinal_permutation_exact": True,
        "probability_semantics": "p1=2*(32768-prob0)",
        "selected_branches": len(truth),
        "selected_symbols": selected_symbols,
        "sha256": legacy.sha256(path),
        "symbol_rows": rows,
        "visited_branches": branches,
        "vocabulary_every_row": VOCABULARY,
    }
    return metadata, probabilities, truth


def encode_and_decode(
    probabilities: np.ndarray, truth: np.ndarray, label: str
) -> bytes:
    if len(probabilities) != len(truth):
        raise ValueError(f"{label} probability/truth lengths differ")
    payload = range_encode(probabilities, truth)
    decoded = range_decode(payload, probabilities)
    if len(decoded) != len(truth) or not np.array_equal(decoded, truth):
        raise ValueError(f"{label} finite arithmetic stream failed decode")
    return payload


def parse_args() -> argparse.Namespace:
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
        "--raw-1g",
        type=Path,
        default=Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9"),
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if BLOCK_SYMBOLS != 499_712:
        raise ValueError("frozen NNCP block arithmetic changed")
    if SELECTION_END - SELECTION_START != BLOCK_SYMBOLS:
        raise ValueError("selected population is not one complete native block")

    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite a closed-block Q1 decision")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_binding = bind_tracked_sources()

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
    inputs = {label: legacy.verify_file(label, path) for label, path in paths.items()}
    inputs["raw_1g"] = verify_raw_1g(args.raw_1g, args.raw_10m)

    q0 = json.loads(args.q0_decision.read_text())
    if q0.get("status") != "PASS" or not q0.get("decision", {}).get(
        "promotion_authorized"
    ):
        raise ValueError("encode-only Q0 does not authorize one mature gate")

    population = verify_symbol_population(args.symbol_map, args.preprocessed)
    expected_symbols = np.memmap(
        args.preprocessed,
        mode="r",
        dtype=">u2",
        shape=(EXECUTION_SYMBOLS,),
    )
    joint = legacy.exact_joint_parent(
        args.joint_p1,
        args.wrt_store,
        args.wrt_dictionary,
        args.raw_10m,
        RAW_START,
        RAW_END,
        args.output_dir,
    )
    if joint["wrt_start_byte"] != WRT_START or joint["wrt_end_byte"] != WRT_END:
        raise ValueError("frozen complete-block WRT boundaries changed")

    full_artifact_names = (
        "teacher_complete_block.nncp",
        "teacher_native_trace.bin",
        "teacher_guard.json",
        "teacher_block.payload",
    )
    if any((args.output_dir / name).exists() for name in full_artifact_names):
        raise RuntimeError(
            "preexisting complete-block artifacts require named quarantine; reuse forbidden"
        )

    with tempfile.TemporaryDirectory(prefix="nncp-closed-block-q1-") as temp_name:
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
        build_environment = clean_environment(os.environ)
        build = subprocess.run(
            ["make", "-C", str(source_root), "-j2"],
            check=False,
            text=True,
            capture_output=True,
            env=build_environment,
        )
        (args.output_dir / "build.stdout").write_text(build.stdout)
        (args.output_dir / "build.stderr").write_text(build.stderr)
        if build.returncode != 0:
            raise RuntimeError("NNCP observer build failed")
        binary = source_root / "nncp"
        library = source_root / "libnc.so"

        original_environment = clean_environment(os.environ)
        original_environment["LD_LIBRARY_PATH"] = str(args.original_binary.parent)
        patched_environment = clean_environment(os.environ)
        patched_environment["LD_LIBRARY_PATH"] = str(source_root)

        print(json.dumps({"stage": "observer_neutrality_smoke"}), flush=True)
        original_smoke = args.output_dir / "smoke_original.nncp"
        patched_off_smoke = args.output_dir / "smoke_patched_off.nncp"
        patched_on_smoke = args.output_dir / "smoke_patched_on.nncp"
        smoke_trace_path = args.output_dir / "smoke_native_trace.bin"
        legacy.run_command(
            legacy.command_for(
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
        legacy.run_command(
            legacy.command_for(
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
        legacy.run_command(
            legacy.command_for(
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
        smoke_payload = encode_and_decode(
            smoke_probabilities, smoke_truth, "smoke converted subset"
        )

        long_archive = args.output_dir / "teacher_complete_block.nncp"
        long_trace_path = args.output_dir / "teacher_native_trace.bin"
        long_guard = args.output_dir / "teacher_guard.json"
        long_environment = dict(patched_environment)
        long_environment["NNCP_NATIVE_TRACE"] = str(long_trace_path.resolve())
        print(
            json.dumps(
                {
                    "stage": "continuous_complete_block_teacher",
                    "max_symbols": EXECUTION_SYMBOLS,
                    "selected_symbols": [SELECTION_START, SELECTION_END],
                }
            ),
            flush=True,
        )
        guard_receipt = legacy.guarded_run(
            legacy.command_for(
                binary,
                args.dictionary,
                args.preprocessed,
                EXECUTION_SYMBOLS,
                long_archive,
            ),
            long_environment,
            long_guard,
            f"{CANDIDATE_ID}_continuous_teacher",
        )
        if guard_receipt.get("status") != "complete" or int(
            guard_receipt.get("returncode", -1)
        ) != 0:
            raise RuntimeError("complete-block teacher guard is not a clean success")

        print(json.dumps({"stage": "verify_complete_block_trace"}), flush=True)
        teacher_trace, teacher_probabilities, teacher_truth = verify_trace(
            long_trace_path,
            expected_symbols,
            EXECUTION_SYMBOLS,
            SELECTION_START,
            SELECTION_END,
        )
        teacher_payload = encode_and_decode(
            teacher_probabilities, teacher_truth, "teacher complete block"
        )
        teacher_payload_path = args.output_dir / "teacher_block.payload"
        teacher_payload_path.write_bytes(teacher_payload)
        if not teacher_payload:
            raise ValueError("complete-block teacher payload is empty")
        memory_clean = (
            not guard_receipt.get("rss_guard_exceeded", False)
            and int(guard_receipt["max_sampled_tree_rss_kib"]) <= LIMIT_KIB
        )
        if not memory_clean:
            raise RuntimeError("complete-block teacher exceeded decimal 10GB")
        build_receipt = {
            "binary": {
                "bytes": binary.stat().st_size,
                "sha256": legacy.sha256(binary),
            },
            "compiler": subprocess.run(
                ["gcc", "--version"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.splitlines()[0],
            "library": {
                "bytes": library.stat().st_size,
                "sha256": legacy.sha256(library),
            },
            "patch": {
                "bytes": patch_path.stat().st_size,
                "sha256": legacy.sha256(patch_path),
            },
        }

    raw_bytes = RAW_END - RAW_START
    teacher_archive_bytes = len(teacher_payload)
    joint_archive_bytes = int(joint["archive_bytes"])
    gain_bytes = joint_archive_bytes - teacher_archive_bytes
    gain_bpm = gain_bytes * 1_000_000.0 / raw_bytes
    promotion = gain_bpm >= GROSS_GATE_BPM
    decision = {
        "schema": "gamma.nncp_v33_libnc_cpu_encode_only_closed_block_q1.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_DISTANT_COMPLETE_BLOCK" if promotion else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Non-decodable full-dictionary teacher headroom only; no constructive "
            "codec, package, forecast, or full-corpus claim."
        ),
        "population": {
            **population,
            "charged_symbol_interval": [SELECTION_START, SELECTION_END],
            "continuous_from_symbol": 0,
            "joint_p1_rows": [WRT_START * 8, WRT_END * 8],
            "raw_bytes": raw_bytes,
            "wrt_byte_interval": [WRT_START, WRT_END],
        },
        "parent": joint,
        "teacher": {
            "continuous_encode_only_archive": {
                "bytes": long_archive.stat().st_size,
                "sha256": legacy.sha256(long_archive),
            },
            "dictionary_accounting": "free teacher/preprocessor information in Q1",
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
            "all_converted_probabilities_legal_nonzero": True,
            "complete_native_block_charged": True,
            "complete_block_execution_order_preserved": True,
            "continuous_teacher_from_symbol_zero": True,
            "decimal_10gb_process_tree_pass": True,
            "joint_window_arithmetic_decode": True,
            "joint_raw_boundaries_exact": True,
            "local_10m_is_receipt_bound_1g_prefix": True,
            "native_original_ordinal_permutation_exact": True,
            "observer_smoke_archive_identity": True,
            "probability_conversion": "p1=2*(32768-prob0)",
            "q0_sampled_perturbation_authorization": True,
            "teacher_window_arithmetic_decode": True,
            "vocabulary_every_row": VOCABULARY,
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
        "source_binding": source_binding,
        "decision": {
            "forecast_bytes": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "next_action": (
                "preregister one distant complete-block teacher replay"
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
