#!/usr/bin/env python3
"""Run the frozen native midpoint bridge on the production NNCP alphabet."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time

from materialize_nncp_midsegment32_indexed_trace_observer import (
    materialize as materialize_midpoint_observer,
)
from materialize_nncp_native_indexed_trace_observer import (
    materialize as materialize_parent_observer,
)
from nncp_symbol_cache32_marginal_qm0 import RangeEncoder
import nncp_libnc_exact_midsegment32_qm2 as q2


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
SOURCE_TAR = q2.SOURCE_TAR
MIDPOINT_PATCH = q2.PATCH
PREPROCESSED = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "dictionary.bin"
)
EXPECTED_RAW = ROOT / "results/nncp_midsegment32_update_qm0_v1/restored.raw"
PACKAGE_DECISION = ROOT / "results/nncp_libnc_midsegment32_cpu_xz_package_qm1_v1/decision.json"
MATURE_DECISION = ROOT / "results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/decision.json"
VERIFY_TRACE = ROOT / "tools/verify_nncp_native_trace.py"
SYMBOLS = 65_536
SYMBOL_BYTES = SYMBOLS * 2
VOCABULARY = 16_392
GAIN_GATE = 3_000
SOURCE_GATE = 260_000
EXPECTED = {
    "source_tar": "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    "preprocessed": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "symbol_prefix": "6e4e2e7d17de3e37de6d81699a132113b4c7bdd330173cad614cdc8a9247e4cb",
    "dictionary": "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1",
    "raw": "a5daeae040c2575ae1c2fd5f3284d73caafa0fcd48c3f546e199ab7c5f1ab7e9",
}
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    command: list[str], *, cwd: Path, environment: dict[str, str] | None = None
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


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def extract_source(target: Path) -> dict[str, object]:
    target.mkdir()
    return run(
        ["tar", "-xzf", str(SOURCE_TAR), "--strip-components=1", "-C", str(target)],
        cwd=target.parent,
    )


def environment(source: Path, trace: Path | None = None) -> dict[str, str]:
    value = os.environ.copy()
    value["LD_LIBRARY_PATH"] = str(source)
    if trace is not None:
        value["NNCP_NATIVE_TRACE"] = str(trace)
    else:
        value.pop("NNCP_NATIVE_TRACE", None)
    value.pop("NNCP_NATIVE_TRACE_FULL_WINDOWS", None)
    value.pop("NNCP_NATIVE_TRACE_CHECKPOINTS", None)
    return value


def encode_command(binary: Path, archive: Path, *, midpoint: bool) -> list[str]:
    command = [
        str(binary),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--n_symb",
        str(VOCABULARY),
        "--dict",
        str(DICTIONARY),
    ]
    if midpoint:
        command.append("--midsegment32")
    command.extend(
        ["--max_size", str(SYMBOLS), "c", str(PREPROCESSED), str(archive)]
    )
    return command


def parse_trace(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) < TRACE_HEADER.size:
        raise ValueError("truncated indexed trace")
    magic, rows, branch_total, trees, checkpoints = TRACE_HEADER.unpack_from(raw)
    if magic != b"NNNTR4\0\0" or rows != SYMBOLS or trees != 0 or checkpoints != 0:
        raise ValueError("indexed trace header mismatch")
    offset = TRACE_HEADER.size
    seen = bytearray(SYMBOLS)
    thirds = [RangeEncoder(), RangeEncoder(), RangeEncoder()]
    ideal_bits = [0.0, 0.0, 0.0]
    observed_branches = 0
    for execution in range(SYMBOLS):
        if offset + TRACE_ROW.size > len(raw):
            raise ValueError("truncated indexed row")
        row = TRACE_ROW.unpack_from(raw, offset)
        offset += TRACE_ROW.size
        original, actual_execution = row[0], row[1]
        symbol, vocabulary, branch_count, has_tree, checkpoint = row[8:]
        if actual_execution != execution or original >= SYMBOLS or seen[original]:
            raise ValueError("invalid indexed execution/original identity")
        seen[original] = 1
        if vocabulary != VOCABULARY or symbol >= VOCABULARY:
            raise ValueError("trace symbol domain mismatch")
        if has_tree or checkpoint:
            raise ValueError("unexpected full-tree or checkpoint row")
        third = min(2, original * 3 // SYMBOLS)
        for _ in range(branch_count):
            if offset + TRACE_BRANCH.size > len(raw):
                raise ValueError("truncated indexed branch")
            probability, bit = TRACE_BRANCH.unpack_from(raw, offset)
            offset += TRACE_BRANCH.size
            if not 1 <= probability < 32768 or bit not in (0, 1):
                raise ValueError("illegal traced branch")
            thirds[third].put_bit(probability, bit)
            realized = probability if bit == 0 else 32768 - probability
            ideal_bits[third] -= math.log2(realized / 32768.0)
            observed_branches += 1
    if offset != len(raw) or observed_branches != branch_total or not all(seen):
        raise ValueError("indexed trace totals mismatch")
    payloads = [coder.finish() for coder in thirds]
    return {
        "rows": rows,
        "branches": observed_branches,
        "third_payload_bytes": [len(payload) for payload in payloads],
        "third_payload_sha256": [hashlib.sha256(payload).hexdigest() for payload in payloads],
        "third_ideal_bits": ideal_bits,
    }


def main() -> int:
    required = [
        SOURCE_TAR,
        MIDPOINT_PATCH,
        PREPROCESSED,
        DICTIONARY,
        EXPECTED_RAW,
        PACKAGE_DECISION,
        MATURE_DECISION,
        VERIFY_TRACE,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing bridge inputs: {missing}")
    if sha256(SOURCE_TAR) != EXPECTED["source_tar"]:
        raise ValueError("source tar mismatch")
    if sha256(PREPROCESSED) != EXPECTED["preprocessed"]:
        raise ValueError("preprocessed stream mismatch")
    if sha256(DICTIONARY) != EXPECTED["dictionary"]:
        raise ValueError("dictionary mismatch")
    if EXPECTED_RAW.stat().st_size != 322_978 or sha256(EXPECTED_RAW) != EXPECTED["raw"]:
        raise ValueError("expected raw bridge population mismatch")
    package = json.loads(PACKAGE_DECISION.read_text())
    package_bytes = int(package["package"]["bytes"])
    if package_bytes > SOURCE_GATE:
        raise ValueError("teacher package exceeds frozen bridge gate")
    mature = json.loads(MATURE_DECISION.read_text())
    if mature.get("decision", {}).get("promotion_authorized") is not True:
        raise ValueError("mature antecedent did not authorize bridge")

    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    symbol_prefix = RESULT / "symbols_65536.be16"
    with PREPROCESSED.open("rb") as source:
        symbol_prefix.write_bytes(source.read(SYMBOL_BYTES))
    if symbol_prefix.stat().st_size != SYMBOL_BYTES or sha256(symbol_prefix) != EXPECTED["symbol_prefix"]:
        raise ValueError("production symbol prefix mismatch")

    paths = {
        "p_clean": RESULT / "P_clean.nncp",
        "p_trace": RESULT / "P_trace.nncp",
        "f_clean": RESULT / "F_clean.nncp",
        "f_trace": RESULT / "F_trace.nncp",
        "p_raw": RESULT / "P_restored.raw",
        "f_raw": RESULT / "F_restored.raw",
        "p_trace_bin": RESULT / "P_trace.bin",
        "f_trace_bin": RESULT / "F_trace.bin",
        "p_cert": RESULT / "P_trace_cert.json",
        "f_cert": RESULT / "F_trace_cert.json",
        "environment": RESULT / "environment.json",
    }
    paths["environment"].write_text(
        json.dumps({"execution_status": "CPU_READY", "device": "cpu", "threads": 4}, sort_keys=True)
        + "\n"
    )
    execution: dict[str, object] = {}
    observer: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="nncp-prod-midpoint-bridge-") as temporary:
        tmp = Path(temporary)
        parent_root = tmp / "parent"
        candidate_root = tmp / "candidate"
        execution["extract_parent"] = extract_source(parent_root)
        execution["extract_candidate"] = extract_source(candidate_root)

        execution["build_parent_clean"] = run(["make", "-j4"], cwd=parent_root)
        parent_binary = parent_root / "nncp"
        print(json.dumps({"event": "P_clean_start"}), flush=True)
        execution["P_clean_encode"] = run(
            encode_command(parent_binary, paths["p_clean"], midpoint=False),
            cwd=parent_root,
            environment=environment(parent_root),
        )
        parent_patch = tmp / "parent_observer.patch"
        materialize_parent_observer(parent_root, parent_patch)
        observer["parent_patch"] = artifact(parent_patch)
        execution["build_parent_observer"] = run(["make", "-j4"], cwd=parent_root)
        print(json.dumps({"event": "P_trace_start"}), flush=True)
        execution["P_trace_encode"] = run(
            encode_command(parent_binary, paths["p_trace"], midpoint=False),
            cwd=parent_root,
            environment=environment(parent_root, paths["p_trace_bin"]),
        )
        execution["P_decode"] = run(
            [str(parent_binary), "-q", "-T", "4", "d", str(paths["p_trace"]), str(paths["p_raw"])],
            cwd=parent_root,
            environment=environment(parent_root),
        )

        execution["midpoint_patch"] = run(
            ["patch", "-p1", "-i", str(MIDPOINT_PATCH)], cwd=candidate_root
        )
        execution["build_F_clean"] = run(["make", "-j4"], cwd=candidate_root)
        candidate_binary = candidate_root / "nncp"
        print(json.dumps({"event": "F_clean_start"}), flush=True)
        execution["F_clean_encode"] = run(
            encode_command(candidate_binary, paths["f_clean"], midpoint=True),
            cwd=candidate_root,
            environment=environment(candidate_root),
        )
        candidate_patch = tmp / "candidate_observer.patch"
        materialize_midpoint_observer(candidate_root, candidate_patch)
        observer["candidate_patch"] = artifact(candidate_patch)
        execution["build_F_observer"] = run(["make", "-j4"], cwd=candidate_root)
        print(json.dumps({"event": "F_trace_start"}), flush=True)
        execution["F_trace_encode"] = run(
            encode_command(candidate_binary, paths["f_trace"], midpoint=True),
            cwd=candidate_root,
            environment=environment(candidate_root, paths["f_trace_bin"]),
        )
        execution["F_decode"] = run(
            [str(candidate_binary), "-q", "-T", "4", "d", str(paths["f_trace"]), str(paths["f_raw"])],
            cwd=candidate_root,
            environment=environment(candidate_root),
        )

        for arm in ("P", "F"):
            execution[f"verify_{arm}_trace"] = run(
                [
                    "python3",
                    str(VERIFY_TRACE),
                    "--trace",
                    str(paths[f"{arm.lower()}_trace_bin"]),
                    "--trace-on-archive",
                    str(paths[f"{arm.lower()}_trace"]),
                    "--trace-off-archive",
                    str(paths[f"{arm.lower()}_clean"]),
                    "--decoded",
                    str(paths[f"{arm.lower()}_raw"]),
                    "--expected-raw",
                    str(EXPECTED_RAW),
                    "--environment",
                    str(paths["environment"]),
                    "--required-execution-status",
                    "CPU_READY",
                    "--expected-symbols",
                    str(symbol_prefix),
                    "--receipt",
                    str(paths[f"{arm.lower()}_cert"]),
                ],
                cwd=ROOT,
            )

    p_trace = parse_trace(paths["p_trace_bin"])
    f_trace = parse_trace(paths["f_trace_bin"])
    p_thirds = p_trace["third_payload_bytes"]
    f_thirds = f_trace["third_payload_bytes"]
    third_gains = [int(p) - int(f) for p, f in zip(p_thirds, f_thirds)]
    ideal_third_gains = [
        (float(p) - float(f)) / 8.0
        for p, f in zip(p_trace["third_ideal_bits"], f_trace["third_ideal_bits"])
    ]
    p_bytes = paths["p_clean"].stat().st_size
    f_bytes = paths["f_clean"].stat().st_size
    actual_gain = p_bytes - f_bytes
    schedule = q2.serialized_schedule_header(paths["f_clean"])
    p_repeat = paths["p_clean"].read_bytes() == paths["p_trace"].read_bytes()
    f_repeat = paths["f_clean"].read_bytes() == paths["f_trace"].read_bytes()
    raw_identity = (
        paths["p_raw"].read_bytes() == EXPECTED_RAW.read_bytes()
        and paths["f_raw"].read_bytes() == EXPECTED_RAW.read_bytes()
    )
    failed: list[str] = []
    if actual_gain < GAIN_GATE:
        failed.append("actual_gain_below_3000")
    if any(value <= 0 for value in third_gains):
        failed.append("original_coordinate_third_nonpositive")
    if not p_repeat or not f_repeat:
        failed.append("observer_or_repeat_archive_mismatch")
    if not raw_identity:
        failed.append("official_raw_inverse_mismatch")
    if not schedule.get("valid") or schedule.get("vocabulary") != VOCABULARY:
        failed.append("serialized_schedule_mismatch")
    promotion = not failed
    decision = {
        "schema": "enwiki9_nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_PRODUCTION_ATTRIBUTION" if promotion else "REJECT",
        "verdict": (
            "authorize_production_P_K_O_OK_F_S_attribution"
            if promotion
            else "retire_native_full_dictionary_midpoint_transfer"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact native CPU P/F bridge on 65,536 production-alphabet symbols. "
            "Teacher-only: no open LibNC source, full-corpus transfer, forecast, or score credit."
        ),
        "population": {"symbols": SYMBOLS, "symbol_bytes": SYMBOL_BYTES, "vocabulary": VOCABULARY, "raw_bytes": 322_978},
        "comparison": {
            "P_archive_bytes": p_bytes,
            "F_archive_bytes": f_bytes,
            "actual_gain_bytes": actual_gain,
            "required_gain_bytes": GAIN_GATE,
            "original_coordinate_third_gain_bytes": third_gains,
            "original_coordinate_ideal_third_gain_bytes": ideal_third_gains,
        },
        "integrity": {
            "P_trace_neutral": p_repeat,
            "F_repeat_and_trace_neutral": f_repeat,
            "P_and_F_raw_inverse_exact": raw_identity,
            "serialized_schedule": schedule,
            "P_trace_certificate": artifact(paths["p_cert"]),
            "F_trace_certificate": artifact(paths["f_cert"]),
        },
        "program_accounting": {
            "teacher_package_bytes": package_bytes,
            "maximum_teacher_package_bytes": SOURCE_GATE,
            "source_eligibility_proven": False,
            "observer_is_proof_only": True,
        },
        "artifacts": {name: artifact(path) for name, path in paths.items()},
        "observer": observer | {"P": p_trace, "F": f_trace},
        "execution": execution,
        "inputs": {
            "source_tar": artifact(SOURCE_TAR),
            "midpoint_patch": artifact(MIDPOINT_PATCH),
            "preprocessed": artifact(PREPROCESSED),
            "dictionary": artifact(DICTIONARY),
            "expected_raw": artifact(EXPECTED_RAW),
            "mature_antecedent": artifact(MATURE_DECISION),
            "package_antecedent": artifact(PACKAGE_DECISION),
        },
        "failed_conditions": failed,
        "decision": {"promotion_authorized": promotion, "verified_full_1g_score_bytes": None, "forecast_bytes": 109_389_323, "target_bytes": 105_000_000},
    }
    (RESULT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
