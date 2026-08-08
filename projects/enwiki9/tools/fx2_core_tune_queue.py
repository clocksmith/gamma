#!/usr/bin/env python3
"""Build and gate fx2 core-tuning candidates through one serialized lane."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PACKAGE = ROOT / "tools" / "fx2_core_tune_package.py"
RECORD = ROOT / "tools" / "record_driver_result.py"
DRIVER = ROOT / "lib" / "driver.py"
PROGRAMS = ROOT / "programs"


@dataclass(frozen=True)
class TuneSpec:
    candidate_id: str
    mixer_context_limit: int
    mixer0_lr_scale: float
    mixer1_lr_scale: float
    lstm_lr_scale: float
    sse_wr_scale_ppm: int
    mixer_decay_t0: int = 1000000
    mixer_decay_t1: int = 5000000
    mixer_decay_t2: int = 25000000
    mixer_decay_p0: int = 1000000
    mixer_decay_p1: int = 700000
    mixer_decay_p2: int = 300000
    mixer_decay_p3: int = 200000


DEFAULT_QUEUE = (
    TuneSpec(
        "fx2_core_tune_title_mctx8000_m0p95_m1p95_lstm1p00_sse1000_v1",
        8000,
        0.95,
        0.95,
        1.00,
        1000,
    ),
    TuneSpec(
        "fx2_core_tune_title_mctx12000_m0p95_m1p95_lstm1p00_sse1000_v1",
        12000,
        0.95,
        0.95,
        1.00,
        1000,
    ),
    TuneSpec(
        "fx2_core_tune_title_mctx10000_m0p95_m1p95_lstm1p00_sse950_v1",
        10000,
        0.95,
        0.95,
        1.00,
        950,
    ),
    TuneSpec(
        "fx2_core_tune_title_mctx10000_m0p95_m1p95_lstm1p00_sse1050_v1",
        10000,
        0.95,
        0.95,
        1.00,
        1050,
    ),
    TuneSpec(
        "fx2_core_tune_title_mctx10000_m0p100_m1p100_lstm1p00_sse1000_v1",
        10000,
        1.00,
        1.00,
        1.00,
        1000,
    ),
)


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def driver_label(limit: int) -> str:
    labels = {
        1024: "1k_driver_gate",
        250000: "250k_driver_gate",
        1000000: "1m_driver_gate",
        10000000: "10m_driver_gate",
        100000000: "100m_driver_gate",
    }
    return labels.get(limit, f"{limit}_driver_gate")


def build_command(spec: TuneSpec) -> list[str]:
    return [
        sys.executable,
        str(PACKAGE),
        "--id",
        spec.candidate_id,
        "--mixer-context-limit",
        str(spec.mixer_context_limit),
        "--mixer0-lr-scale",
        str(spec.mixer0_lr_scale),
        "--mixer1-lr-scale",
        str(spec.mixer1_lr_scale),
        "--lstm-lr-scale",
        str(spec.lstm_lr_scale),
        "--sse-wr-scale-ppm",
        str(spec.sse_wr_scale_ppm),
        "--mixer-decay-t0",
        str(spec.mixer_decay_t0),
        "--mixer-decay-t1",
        str(spec.mixer_decay_t1),
        "--mixer-decay-t2",
        str(spec.mixer_decay_t2),
        "--mixer-decay-p0",
        str(spec.mixer_decay_p0),
        "--mixer-decay-p1",
        str(spec.mixer_decay_p1),
        "--mixer-decay-p2",
        str(spec.mixer_decay_p2),
        "--mixer-decay-p3",
        str(spec.mixer_decay_p3),
        "--compiler",
        "g++",
    ]


def driver_command(spec: TuneSpec, limit: int, archive_ceiling: int | None = None) -> list[str]:
    command = [
        sys.executable,
        str(DRIVER),
        spec.candidate_id,
        "--limit",
        str(limit),
        "--check-determinism",
    ]
    if archive_ceiling is not None:
        command.extend(
            [
                "--archive-ceiling",
                str(archive_ceiling),
                "--determinism-archive-ceiling",
                str(archive_ceiling),
            ]
        )
    return command


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_result(stdout: str) -> dict[str, Any] | None:
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


def deterministic(result: dict[str, Any]) -> bool:
    determinism = result.get("determinism")
    return isinstance(determinism, dict) and determinism.get("single_host_byte_equal") is True


def record_result(spec: TuneSpec, result: dict[str, Any], status: str, verdict: str) -> None:
    stamp = str(result["timestamp"]).replace(":", "")
    result_path = ROOT / "results" / spec.candidate_id / f"{stamp}.json"
    cmd = [
        sys.executable,
        str(RECORD),
        spec.candidate_id,
        "--label",
        driver_label(int(result["data_size"])),
        "--result",
        str(result_path),
        "--status",
        status,
        "--verdict",
        verdict,
    ]
    proc = run_command(cmd)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())


def parse_tune_spec(value: str) -> TuneSpec:
    parts = value.split(":")
    if len(parts) not in {6, 13}:
        raise SystemExit(
            "--spec values must be ID:MCTX:M0:M1:LSTM:SSEPPM or "
            "ID:MCTX:M0:M1:LSTM:SSEPPM:T0:T1:T2:P0:P1:P2:P3"
        )
    candidate_id, raw_mctx, raw_m0, raw_m1, raw_lstm, raw_sse = parts[:6]
    decay_values = (
        (1000000, 5000000, 25000000, 1000000, 700000, 300000, 200000)
        if len(parts) == 6
        else tuple(int(part) for part in parts[6:])
    )
    return TuneSpec(
        candidate_id,
        int(raw_mctx),
        float(raw_m0),
        float(raw_m1),
        float(raw_lstm),
        int(raw_sse),
        *decay_values,
    )


def planned_specs(ids: list[str], values: list[str]) -> list[TuneSpec]:
    if ids and values:
        raise SystemExit("use --candidate for default queue entries or --spec for explicit mutations")
    if values:
        return [parse_tune_spec(value) for value in values]
    if not ids:
        return list(DEFAULT_QUEUE)
    known = {spec.candidate_id: spec for spec in DEFAULT_QUEUE}
    missing = [candidate_id for candidate_id in ids if candidate_id not in known]
    if missing:
        raise SystemExit(f"unknown default candidate id(s): {', '.join(missing)}")
    return [known[candidate_id] for candidate_id in ids]


def print_plan(specs: list[TuneSpec], gate_sizes: list[int]) -> None:
    payload = []
    for spec in specs:
        payload.append(
            {
                "id": spec.candidate_id,
                "knobs": {
                    "mixer_context_limit": spec.mixer_context_limit,
                    "mixer0_lr_scale": spec.mixer0_lr_scale,
                    "mixer1_lr_scale": spec.mixer1_lr_scale,
                    "lstm_lr_scale": spec.lstm_lr_scale,
                    "sse_wr_scale_ppm": spec.sse_wr_scale_ppm,
                    "mixer_decay_t0": spec.mixer_decay_t0,
                    "mixer_decay_t1": spec.mixer_decay_t1,
                    "mixer_decay_t2": spec.mixer_decay_t2,
                    "mixer_decay_p0": spec.mixer_decay_p0,
                    "mixer_decay_p1": spec.mixer_decay_p1,
                    "mixer_decay_p2": spec.mixer_decay_p2,
                    "mixer_decay_p3": spec.mixer_decay_p3,
                },
                "program_dir": rel(PROGRAMS / spec.candidate_id),
                "gates": gate_sizes,
            }
        )
    print(json.dumps(payload, indent=2))


def run_queue(specs: list[TuneSpec], gate_sizes: list[int], archive_ceiling: dict[int, int]) -> int:
    for spec in specs:
        program_dir = PROGRAMS / spec.candidate_id
        if not (program_dir / "program.py").exists():
            build = run_command(build_command(spec))
            if build.returncode != 0:
                print(build.stdout, end="")
                print(build.stderr, end="", file=sys.stderr)
                return build.returncode

        for limit in gate_sizes:
            ceiling = archive_ceiling.get(limit)
            proc = run_command(driver_command(spec, limit, ceiling))
            if proc.returncode == BUSY_CODE:
                print(json.dumps({"status": "lock_busy", "candidate": spec.candidate_id, "limit": limit}))
                return BUSY_CODE
            if proc.returncode != 0:
                print(proc.stdout, end="")
                print(proc.stderr, end="", file=sys.stderr)
                return proc.returncode
            result = parse_result(proc.stdout)
            if not result:
                print(proc.stdout, end="")
                print(proc.stderr, end="", file=sys.stderr)
                return 2

            ok = result.get("roundtrip_ok") is True and deterministic(result)
            archive = int(result["compressed_size"])
            archive_ok = ceiling is None or archive < ceiling
            status = "active" if ok and archive_ok else "measured_negative"
            verdict = (
                f"Exact {driver_label(limit)} passed roundtrip/determinism with archive={archive}."
                if ok and archive_ok
                else f"Exact {driver_label(limit)} failed promotion: roundtrip_deterministic={ok}, archive={archive}, ceiling={ceiling}."
            )
            record_result(spec, result, status, verdict)
            print(
                json.dumps(
                    {
                        "candidate": spec.candidate_id,
                        "limit": limit,
                        "archive": archive,
                        "program_size": result.get("program_size"),
                        "status": status,
                        "ceiling": ceiling,
                    },
                    sort_keys=True,
                )
            )
            if status != "active":
                break
    return 0


def parse_archive_ceiling(values: list[str]) -> dict[int, int]:
    out: dict[int, int] = {}
    for value in values:
        if ":" not in value:
            raise SystemExit("--archive-ceiling values must be LIMIT:BYTES")
        raw_limit, raw_bytes = value.split(":", 1)
        out[int(raw_limit)] = int(raw_bytes)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--spec", action="append", default=[])
    parser.add_argument("--gate-size", type=int, action="append", default=[])
    parser.add_argument("--archive-ceiling", action="append", default=[])
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    gate_sizes = args.gate_size or [1024, 250000, 1000000]
    specs = planned_specs(args.candidate, args.spec)
    ceilings = parse_archive_ceiling(args.archive_ceiling)
    if not args.run:
        print_plan(specs, gate_sizes)
        return 0
    return run_queue(specs, gate_sizes, ceilings)


if __name__ == "__main__":
    raise SystemExit(main())
