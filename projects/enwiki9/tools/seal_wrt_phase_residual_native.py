#!/usr/bin/env python3
"""Compile and seal the frozen WRT phase residual integration component."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import re
import subprocess
import tempfile

from seal_wrt_hashed_residual_online import artifact, sha256


RESULT_PATTERN = re.compile(
    r"rows=(?P<rows>\d+) baseline_payload_bytes=(?P<baseline>\d+) "
    r"candidate_payload_bytes=(?P<candidate>\d+) exact_saved_bytes=(?P<saved>-?\d+) "
    r"state_bytes=(?P<state>\d+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--endpoint-overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def parse_result(output: str) -> dict[str, int]:
    match = RESULT_PATTERN.fullmatch(output.strip())
    if match is None:
        raise ValueError(f"unexpected replay output: {output!r}")
    return {key: int(value) for key, value in match.groupdict().items()}


def main() -> int:
    args = parse_args()
    root = (args.repo_root or Path(__file__).resolve().parents[3]).resolve()
    overlay = args.endpoint_overlay.resolve()
    tools = root / "projects/enwiki9/tools"
    header = tools / "wrt_phase_residual_native.h"
    source = tools / "wrt_phase_residual_native.cpp"
    replay = tools / "wrt_phase_residual_native_replay.cpp"
    p1 = overlay / "layer0_mixer10_over_endpoint428_nativeq16_v1.p1"
    store = overlay / "input.wrt.store"
    compiler = subprocess.run(
        ["g++", "--version"], check=True, text=True, capture_output=True
    ).stdout.splitlines()[0]
    binary_artifacts = []
    replay_results = []
    with tempfile.TemporaryDirectory(prefix="wrt-phase-native-") as temporary:
        temporary_root = Path(temporary)
        for attempt in range(2):
            binary = temporary_root / f"build{attempt}" / "replay"
            binary.parent.mkdir()
            command = [
                "g++",
                "-std=c++17",
                "-O3",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(source),
                str(replay),
                "-o",
                str(binary),
            ]
            subprocess.run(command, check=True)
            binary_artifacts.append({"bytes": binary.stat().st_size, "sha256": sha256(binary)})
            completed = subprocess.run(
                [str(binary), str(p1), str(store)],
                check=True,
                text=True,
                capture_output=True,
            )
            replay_results.append(parse_result(completed.stdout))
    if binary_artifacts[0] != binary_artifacts[1]:
        raise ValueError("clean builds are not byte-identical")
    if replay_results[0] != replay_results[1]:
        raise ValueError("replay results differ")
    result = replay_results[0]
    if result != {
        "rows": 4_805_936,
        "baseline": 173_849,
        "candidate": 173_808,
        "saved": 41,
        "state": 13_615_104,
    }:
        raise ValueError(f"unexpected frozen replay result: {result}")
    source_payload = header.read_bytes() + source.read_bytes()
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_phase_residual_native_component",
        "evidence_level": "constructive_component_exact_p1_replay",
        "compiler": compiler,
        "compile_flags": ["-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror"],
        "sources": {
            "header": artifact(root, header),
            "implementation": artifact(root, source),
            "replay_harness": artifact(root, replay),
            "component_concatenated_gzip9_bytes": len(
                gzip.compress(source_payload, compresslevel=9, mtime=0)
            ),
        },
        "input_artifacts": {
            "layer0_p1": {
                "logical_name": p1.name,
                "bytes": p1.stat().st_size,
                "sha256": sha256(p1),
                "availability": "local_nonproof_overlay_not_in_git",
            },
            "wrt_store": {
                "logical_name": store.name,
                "bytes": store.stat().st_size,
                "sha256": sha256(store),
                "availability": "local_nonproof_overlay_not_in_git",
            },
        },
        "clean_builds": binary_artifacts,
        "exact_replay": {
            "rows": result["rows"],
            "baseline_payload_bytes": result["baseline"],
            "candidate_payload_bytes": result["candidate"],
            "saved_bytes": result["saved"],
            "saved_bytes_per_million_raw": float(result["saved"]),
            "state_bytes": result["state"],
            "replay_count": 2,
            "replay_results_identical": True,
        },
        "integration_contract": {
            "predict": "call WrtPhaseResidual::Predict with the pair/layer0 final P1 before arithmetic coding",
            "perceive": "call WrtPhaseResidual::Perceive after coding each true bit",
            "payload_bytes": 0,
            "decoder_state_rebuilt_online": True,
        },
        "claim_boundary": (
            "This proves clean-build and exact P1 replay identity for the frozen component. "
            "It is not a combined native archive, roundtrip, runtime, or full-corpus proof."
        ),
        "promotion_authorized": False,
    }
    output = args.output or (
        root
        / "projects/enwiki9/results/fx2_reference_residual_v1/"
        "wrt-phase-residual-native-component.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
