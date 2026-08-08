#!/usr/bin/env python3
"""Build and gate native fx2 typed-anchor soft-state candidates."""

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
class SoftSpec:
    candidate_id: str
    typed_anchor_soft_sse_weight: float
    typed_anchor_context_mode: int = 0
    mixer_context_limit: int = 8000
    mixer0_lr_scale: float = 1.0
    mixer1_lr_scale: float = 0.95
    lstm_lr_scale: float = 1.0
    sse_wr_scale_ppm: int = 1000
    mixer_decay_t0: int = 500000
    mixer_decay_t1: int = 3000000
    mixer_decay_t2: int = 16000000
    mixer_decay_p0: int = 1000000
    mixer_decay_p1: int = 600000
    mixer_decay_p2: int = 250000
    mixer_decay_p3: int = 125000


DEFAULT_QUEUE = (
    SoftSpec("fx2_typed_anchor_soft_mode_sse_v1", 0.0002, 6),
    SoftSpec("fx2_typed_anchor_soft_field_sse_v1", 0.0002, 5),
    SoftSpec("fx2_typed_anchor_soft_field_mode_sse_v1", 0.0002, 1),
    SoftSpec("fx2_typed_anchor_soft_word_sig_sse_v1", 0.0002, 2),
    SoftSpec("fx2_typed_anchor_soft_field_word_sse_v1", 0.0002, 3),
    SoftSpec("fx2_typed_anchor_soft_sse_v1", 0.0002, 0),
)


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def driver_label(limit: int) -> str:
    labels = {
        1024: "1k_driver_gate",
        250000: "250k_driver_gate",
        1000000: "1m_driver_gate",
        10000000: "10m_driver_gate",
        100000000: "100m_driver_gate",
    }
    return labels.get(limit, f"{limit}_driver_gate")


def build_command(spec: SoftSpec) -> list[str]:
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
        "--typed-anchor-soft-sse",
        "--typed-anchor-soft-sse-weight",
        str(spec.typed_anchor_soft_sse_weight),
        "--typed-anchor-context-mode",
        str(spec.typed_anchor_context_mode),
        "--compiler",
        "g++",
    ]


def driver_command(spec: SoftSpec, limit: int, archive_ceiling: int | None = None) -> list[str]:
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


def record_result(spec: SoftSpec, result: dict[str, Any], status: str, verdict: str) -> None:
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


def parse_soft_spec(value: str) -> SoftSpec:
    parts = value.split(":")
    if len(parts) not in {2, 3, 15}:
        raise SystemExit(
            "--spec values must be ID:WEIGHT, ID:WEIGHT:MODE, or "
            "ID:WEIGHT:MODE:MCTX:M0:M1:LSTM:SSEPPM:T0:T1:T2:P0:P1:P2:P3"
        )
    candidate_id, raw_weight = parts[:2]
    if len(parts) == 2:
        return SoftSpec(candidate_id, float(raw_weight))
    raw_mode = parts[2]
    if len(parts) == 3:
        return SoftSpec(candidate_id, float(raw_weight), int(raw_mode))
    raw_mctx, raw_m0, raw_m1, raw_lstm, raw_sse = parts[3:8]
    decay_values = tuple(int(part) for part in parts[8:])
    return SoftSpec(
        candidate_id,
        float(raw_weight),
        int(raw_mode),
        int(raw_mctx),
        float(raw_m0),
        float(raw_m1),
        float(raw_lstm),
        int(raw_sse),
        *decay_values,
    )


def planned_specs(ids: list[str], values: list[str]) -> list[SoftSpec]:
    if ids and values:
        raise SystemExit("use --candidate for default queue entries or --spec for explicit mutations")
    if values:
        return [parse_soft_spec(value) for value in values]
    if not ids:
        return list(DEFAULT_QUEUE)
    known = {spec.candidate_id: spec for spec in DEFAULT_QUEUE}
    missing = [candidate_id for candidate_id in ids if candidate_id not in known]
    if missing:
        raise SystemExit(f"unknown default candidate id(s): {', '.join(missing)}")
    return [known[candidate_id] for candidate_id in ids]


def print_plan(specs: list[SoftSpec], gate_sizes: list[int]) -> None:
    payload = []
    for spec in specs:
        payload.append(
            {
                "id": spec.candidate_id,
                "knobs": {
                    "typed_anchor_soft_sse": True,
                    "typed_anchor_soft_sse_weight": spec.typed_anchor_soft_sse_weight,
                    "typed_anchor_context_mode": spec.typed_anchor_context_mode,
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


def run_queue(
    specs: list[SoftSpec],
    gate_sizes: list[int],
    archive_ceiling: dict[int, int],
    rebuild: bool,
) -> int:
    for spec in specs:
        program_dir = PROGRAMS / spec.candidate_id
        if rebuild or not (program_dir / "program.py").exists():
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
                f"Exact {driver_label(limit)} typed-anchor soft-SSE gate passed "
                f"roundtrip/determinism with archive={archive}."
                if ok and archive_ok
                else (
                    f"Exact {driver_label(limit)} typed-anchor soft-SSE gate failed "
                    f"promotion: roundtrip_deterministic={ok}, archive={archive}, "
                    f"ceiling={ceiling}."
                )
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
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    gate_sizes = args.gate_size or [1024, 250000, 1000000]
    specs = planned_specs(args.candidate, args.spec)
    ceilings = parse_archive_ceiling(args.archive_ceiling)
    if not args.run:
        print_plan(specs, gate_sizes)
        return 0
    return run_queue(specs, gate_sizes, ceilings, args.rebuild)


if __name__ == "__main__":
    raise SystemExit(main())
