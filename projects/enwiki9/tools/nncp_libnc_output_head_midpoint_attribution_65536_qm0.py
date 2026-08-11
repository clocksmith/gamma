#!/usr/bin/env python3
"""Run the frozen production P/K/O/OK/F/S midpoint attribution gate."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time

import nncp_libnc_full_dictionary_midsegment32_65536_qm0 as bridge
from materialize_nncp_midsegment32_indexed_trace_observer import (
    materialize as materialize_observer,
)
from materialize_nncp_output_head_attribution import materialize


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_output_head_midpoint_attribution_65536_qm0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
BRIDGE = ROOT / "results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/decision.json"
PARITY = ROOT / "results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json"
MATERIALIZER = ROOT / "tools/materialize_nncp_output_head_attribution.py"
SOURCE_TAR = bridge.SOURCE_TAR
MIDPOINT_PATCH = PROGRAM / "nncp_midsegment32.patch"
PREPROCESSED = bridge.PREPROCESSED
DICTIONARY = bridge.DICTIONARY
EXPECTED_RAW = bridge.EXPECTED_RAW
SYMBOLS = 65_536
VOCABULARY = 16_392
ARMS = {"P": 0, "F": 1, "K": 2, "O": 3, "OK": 4, "S": 5}
SOURCE_GATE = 65_536
SCHEDULE_OFFSET = 18
STATE_RE = re.compile(
    r"ATTR_STATE arm=(\d+) block=(\d+) step=(\d+) params=([0-9a-f]{8}) memory=([0-9a-f]{8})"
)
GRAD_RE = re.compile(r"ATTR_GRAD arm=(\d+) kind=(weight|bias) hash=([0-9a-f]{8})")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def execute(
    command: list[str], *, cwd: Path, environment: dict[str, str], log: Path
) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    log.write_bytes(completed.stderr)
    return {
        "command": command,
        "elapsed_seconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stderr_log": artifact(log),
    }


def environment(source: Path, trace: Path | None = None) -> dict[str, str]:
    value = os.environ.copy()
    value["LD_LIBRARY_PATH"] = str(source)
    if trace is None:
        value.pop("NNCP_NATIVE_TRACE", None)
    else:
        value["NNCP_NATIVE_TRACE"] = str(trace)
    value.pop("NNCP_ATTRIBUTION_MIDPOINT_ONLY", None)
    value.pop("NNCP_ATTRIBUTION_DUMP_GRAD", None)
    return value


def encode_command(binary: Path, archive: Path, arm: int) -> list[str]:
    return [
        str(binary), "-q", "-T", "4", "--profile", "enwik9",
        "--n_symb", str(VOCABULARY), "--dict", str(DICTIONARY),
        "--midpoint_arm", str(arm), "--max_size", str(SYMBOLS),
        "c", str(PREPROCESSED), str(archive),
    ]


def parsed_payload(path: Path, arm: int) -> bytes:
    raw = path.read_bytes()
    if len(raw) <= SCHEDULE_OFFSET or raw[SCHEDULE_OFFSET] != arm:
        raise ValueError(f"serialized schedule mismatch: {path}")
    return raw[:SCHEDULE_OFFSET] + raw[SCHEDULE_OFFSET + 1 :]


def state_rows(log: Path, arm: int) -> list[tuple[str, ...]]:
    rows = []
    for match in STATE_RE.finditer(log.read_text(errors="replace")):
        if int(match.group(1)) != arm:
            raise ValueError(f"wrong arm in state witness: {log}")
        rows.append(match.groups()[1:])
    return rows


def gradient_rows(log: Path, arm: int) -> list[tuple[str, str]]:
    rows = []
    for match in GRAD_RE.finditer(log.read_text(errors="replace")):
        if int(match.group(1)) != arm:
            raise ValueError(f"wrong arm in gradient witness: {log}")
        rows.append((match.group(2), match.group(3)))
    return rows


def source_package(path: Path) -> dict[str, object]:
    members = [PROGRAM / "program.py", MIDPOINT_PATCH, MATERIALIZER, Path(__file__)]
    with tempfile.TemporaryDirectory(prefix="nncp-attribution-package-") as temporary:
        tar_path = Path(temporary) / "source.tar"
        with tarfile.open(tar_path, "w") as archive:
            for member in members:
                archive.add(member, arcname=member.relative_to(ROOT))
        path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    return artifact(path)


def main() -> int:
    required = [BRIDGE, PARITY, SOURCE_TAR, MIDPOINT_PATCH, MATERIALIZER,
                PREPROCESSED, DICTIONARY, EXPECTED_RAW]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing attribution inputs: {missing}")
    bridge_decision = json.loads(BRIDGE.read_text())
    parity_decision = json.loads(PARITY.read_text())
    if bridge_decision.get("verdict") != "authorize_production_P_K_O_OK_F_S_attribution":
        raise ValueError("production bridge did not authorize attribution")
    if parity_decision.get("verdict") != "authorize_production_P_K_O_OK_F_S_attribution":
        raise ValueError("open production parity did not authorize attribution")
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)

    package = source_package(RESULT / "incremental_source.tar.xz")
    execution: dict[str, object] = {}
    archives: dict[str, dict[str, object]] = {}
    traces: dict[str, dict[str, object]] = {}
    raw_ok: dict[str, bool] = {}
    state: dict[str, list[tuple[str, ...]]] = {}
    gradients: dict[str, list[tuple[str, str]]] = {}

    with tempfile.TemporaryDirectory(prefix="nncp-native-attribution-") as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        execution["extract"] = bridge.extract_source(source)
        execution["midpoint_patch"] = bridge.run(
            ["patch", "-p1", "-i", str(MIDPOINT_PATCH)], cwd=source
        )
        materialize(source)
        execution["build_clean"] = bridge.run(["make", "-j4"], cwd=source)
        binary = source / "nncp"

        for name, arm in ARMS.items():
            archive = RESULT / f"{name}_clean.nncp"
            log = RESULT / f"{name}_clean.stderr"
            print(json.dumps({"event": "clean_encode_start", "arm": name}), flush=True)
            execution[f"{name}_clean_encode"] = execute(
                encode_command(binary, archive, arm), cwd=source,
                environment=environment(source), log=log,
            )
            archives[f"{name}_clean"] = artifact(archive)
            state[name] = state_rows(log, arm)
            gradients[name] = gradient_rows(log, arm)

        marker = "\n/* observer anchors: if (s->midsegment32) if (s->midsegment32) */\n"
        nncp_source = source / "nncp.c"
        nncp_source.write_text(nncp_source.read_text() + marker)
        observer_patch = RESULT / "indexed_observer.patch"
        materialize_observer(source, observer_patch)
        nncp_source.write_text(nncp_source.read_text().replace(marker, ""))
        execution["build_observer"] = bridge.run(["make", "-j4"], cwd=source)

        for name, arm in ARMS.items():
            archive = RESULT / f"{name}_repeat.nncp"
            trace = RESULT / f"{name}_trace.bin"
            log = RESULT / f"{name}_repeat.stderr"
            print(json.dumps({"event": "repeat_encode_start", "arm": name}), flush=True)
            execution[f"{name}_repeat_encode"] = execute(
                encode_command(binary, archive, arm), cwd=source,
                environment=environment(source, trace), log=log,
            )
            decoded = RESULT / f"{name}_restored.raw"
            decode_log = RESULT / f"{name}_decode.stderr"
            print(json.dumps({"event": "decode_start", "arm": name}), flush=True)
            execution[f"{name}_decode"] = execute(
                [str(binary), "-q", "-T", "4", "d", str(archive), str(decoded)],
                cwd=source, environment=environment(source), log=decode_log,
            )
            archives[f"{name}_repeat"] = artifact(archive)
            traces[name] = bridge.parse_trace(trace)
            raw_ok[name] = decoded.read_bytes() == EXPECTED_RAW.read_bytes()
            if state[name] != state_rows(log, arm):
                raise ValueError(f"repeat state trajectory mismatch: {name}")
            if gradients[name] != gradient_rows(log, arm):
                raise ValueError(f"repeat gradient trajectory mismatch: {name}")

    bridge_comparison = bridge_decision["comparison"]
    bridge_p = int(bridge_comparison["P_archive_bytes"])
    bridge_f = int(bridge_comparison["F_archive_bytes"])
    full_gain = int(bridge_comparison["actual_gain_bytes"])
    bridge_thirds = [int(value) for value in bridge_comparison["original_coordinate_third_gain_bytes"]]
    retain_gate = math.ceil(0.80 * full_gain)
    shifted_gate = math.ceil(0.10 * full_gain)
    third_gates = [math.ceil(0.80 * value) for value in bridge_thirds]
    sizes = {name: int(archives[f"{name}_clean"]["bytes"]) for name in ARMS}
    o_gain = bridge_p - sizes["O"]
    shifted_margin = sizes["S"] - sizes["O"]
    o_thirds = [
        int(p) - int(o)
        for p, o in zip(
            traces["P"]["third_payload_bytes"], traces["O"]["third_payload_bytes"]
        )
    ]
    repeats = {
        name: (RESULT / f"{name}_clean.nncp").read_bytes()
        == (RESULT / f"{name}_repeat.nncp").read_bytes()
        for name in ARMS
    }
    pk_payload = parsed_payload(RESULT / "P_clean.nncp", ARMS["P"]) == parsed_payload(
        RESULT / "K_clean.nncp", ARMS["K"]
    )
    ook_payload = parsed_payload(RESULT / "O_clean.nncp", ARMS["O"]) == parsed_payload(
        RESULT / "OK_clean.nncp", ARMS["OK"]
    )
    pk_state = state["P"] == state["K"]
    ook_state = state["O"] == state["OK"]
    ook_gradients = gradients["O"] == gradients["OK"]

    failed: list[str] = []
    checks = {
        "bridge_gain_at_least_3000": full_gain >= 3_000,
        "F_size_reproduces_bridge": sizes["F"] == bridge_f,
        "O_retains_80_percent": o_gain >= retain_gate,
        "O_beats_shifted_control": shifted_margin >= shifted_gate,
        "O_thirds_retain_80_percent": all(
            actual >= gate and actual > 0 for actual, gate in zip(o_thirds, third_gates)
        ),
        "P_K_equal_length": sizes["P"] == sizes["K"],
        "P_K_payload_identical": pk_payload,
        "P_K_state_trajectory_identical": pk_state,
        "O_OK_equal_length": sizes["O"] == sizes["OK"],
        "O_OK_payload_identical": ook_payload,
        "O_OK_state_trajectory_identical": ook_state,
        "O_OK_gradient_trajectory_identical": ook_gradients,
        "all_repeats_identical": all(repeats.values()),
        "all_raw_inverses_exact": all(raw_ok.values()),
        "incremental_source_within_gate": int(package["bytes"]) <= SOURCE_GATE,
    }
    failed.extend(name for name, passed in checks.items() if not passed)
    promotion = not failed
    decision = {
        "schema": "enwiki9_nncp_libnc_output_head_midpoint_attribution_65536_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_GRAM_MIDAS" if promotion else "REJECT",
        "verdict": (
            "authorize_nncp_gram_midas_full_hidden_65536_qm0_v1"
            if promotion else "retire_exact_output_head_midpoint_attribution"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": "Exact production-alphabet LibNC teacher attribution; no open final codec, full-corpus transfer, or score credit.",
        "bridge": {"P_bytes": bridge_p, "F_bytes": bridge_f, "gain_bytes": full_gain},
        "thresholds": {
            "O_gain_bytes": retain_gate,
            "O_max_archive_bytes": bridge_p - retain_gate,
            "O_over_S_margin_bytes": shifted_gate,
            "third_gain_bytes": third_gates,
            "incremental_source_bytes": SOURCE_GATE,
        },
        "comparison": {
            "archive_bytes": sizes,
            "O_gain_bytes": o_gain,
            "O_over_S_margin_bytes": shifted_margin,
            "O_original_coordinate_third_gain_bytes": o_thirds,
        },
        "integrity": {
            "checks": checks,
            "repeat_identity": repeats,
            "raw_inverse_exact": raw_ok,
            "P_K_payload_identity": pk_payload,
            "P_K_state_trajectory_identity": pk_state,
            "O_OK_payload_identity": ook_payload,
            "O_OK_state_trajectory_identity": ook_state,
            "O_OK_gradient_trajectory_identity": ook_gradients,
        },
        "source_package": package,
        "archives": archives,
        "traces": traces,
        "execution": execution,
        "antecedents": {"bridge": artifact(BRIDGE), "parity": artifact(PARITY)},
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
            "target_bytes": 105_000_000,
        },
    }
    (RESULT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
