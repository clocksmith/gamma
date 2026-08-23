#!/usr/bin/env python3
"""Build and repeat the zero-authority WIKI-PDA impossibility scanner."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/enwiki9"
CANDIDATE_ID = "wiki_pda_structural_replay_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
SOURCE = PROJECT / "tools/wiki_pda_structural_replay_q0_v1.cpp"
CONTRACT = PROJECT / "operations/planning/wiki_pda_structural_replay_q0_v1.json"
PROPOSAL = (
    PROJECT
    / "operations/adaptive/proposals/proposed/000_wiki_pda_structural_replay_q0_v1.json"
)
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
INPUT = Path(
    "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
    "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin"
)
INPUT_BYTES = 587_138_826
INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
REQUIRED_GROSS = 4_079_243
COMPILER = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17"
)
COMPILE_FLAGS = [
    "-std=c++17",
    "-O2",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-march=x86-64",
    "-mtune=generic",
]
ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def proc_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text().split()[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def assert_exclusive_host_released() -> None:
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    pid = lease.get("pid")
    start_ticks = lease.get("proc_start_ticks")
    if isinstance(pid, int) and proc_start_ticks(pid) == start_ticks:
        raise RuntimeError(f"exclusive full-1G lease remains active for PID {pid}")
    codec_pid = lease.get("codec_pid")
    if isinstance(codec_pid, int) and Path(f"/proc/{codec_pid}").exists():
        raise RuntimeError(f"exclusive full-1G codec PID {codec_pid} still exists")


def command(
    step_id: str,
    argv: list[str],
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        env=ENVIRONMENT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    return {
        "id": step_id,
        "argv": argv,
        "cwd": str(ROOT),
        "environment": ENVIRONMENT,
        "returncode": completed.returncode,
        "stdout": artifact(stdout_path),
        "stderr": artifact(stderr_path),
    }


def main() -> int:
    assert_exclusive_host_released()
    for path in (SOURCE, CONTRACT, PROPOSAL, INPUT, COMPILER):
        if not path.is_file():
            raise FileNotFoundError(path)
    if INPUT.stat().st_size != INPUT_BYTES or sha256(INPUT) != INPUT_SHA256:
        raise RuntimeError("transformed-ready population identity mismatch")
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)

    binary = RESULT / CANDIDATE_ID
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.wiki_pda_structural_replay_decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "running",
        "claim_authority": "none",
        "score_credit_bytes": 0,
        "promotion_authorized": False,
        "population": artifact(INPUT),
        "contract": artifact(CONTRACT),
        "proposal": artifact(PROPOSAL),
        "source": artifact(SOURCE),
        "compiler": artifact(COMPILER),
        "compile_flags": COMPILE_FLAGS,
    }
    try:
        compile_argv = [str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)]
        decision["compile"] = command(
            "compile",
            compile_argv,
            RESULT / "compile.stdout",
            RESULT / "compile.stderr",
        )
        if decision["compile"]["returncode"] != 0:
            raise RuntimeError("scanner compilation failed")
        decision["scanner"] = artifact(binary)

        scan_argv = [
            str(binary),
            "--input",
            str(INPUT),
            "--score-start",
            "0",
            "--score-end",
            str(INPUT_BYTES),
            "--required-gross",
            str(REQUIRED_GROSS),
        ]
        decision["scan_a"] = command(
            "scan_a",
            scan_argv,
            RESULT / "scan_a.json",
            RESULT / "scan_a.stderr",
        )
        if decision["scan_a"]["returncode"] != 0:
            raise RuntimeError("scanner Arm A failed")
        decision["scan_b"] = command(
            "scan_b",
            scan_argv,
            RESULT / "scan_b.json",
            RESULT / "scan_b.stderr",
        )
        if decision["scan_b"]["returncode"] != 0:
            raise RuntimeError("scanner Arm B failed")

        scan_a_path = RESULT / "scan_a.json"
        scan_b_path = RESULT / "scan_b.json"
        repeat_identity = scan_a_path.read_bytes() == scan_b_path.read_bytes()
        if not repeat_identity:
            raise RuntimeError("repeat scanner summaries differ")
        summary = json.loads(scan_a_path.read_text(encoding="utf-8"))
        if summary.get("schema") != "gamma.enwiki9.wiki_pda_structural_replay_scan.v1":
            raise RuntimeError("scanner summary schema mismatch")
        absolute_pass = summary.get("absolute_ceiling_pass") is True
        decision.update(
            {
                "operational_status": "terminal",
                "repeat_summary_byte_identity_pass": True,
                "summary": summary,
                "absolute_ceiling_pass": absolute_pass,
                "scientific_verdict": (
                    "authorize_donor_surprise_trace_zero_credit"
                    if absolute_pass
                    else "retire_wiki_pda_structural_replay_absolute_ceiling_subscale"
                ),
                "next_authority": (
                    "donor-surprise tracing only"
                    if absolute_pass
                    else "none; one materially different orthogonal family may be proposed from this terminal evidence"
                ),
            }
        )
    except Exception as exc:
        decision.update(
            {
                "operational_status": "terminal_infrastructure_failure",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "scientific_verdict": "none",
                "next_authority": (
                    "one correction-only implementation successor with unchanged "
                    "population, parser, controls, thresholds, and accounting"
                ),
            }
        )
        write_json(RESULT / "decision.json", decision)
        return 1

    write_json(RESULT / "decision.json", decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
