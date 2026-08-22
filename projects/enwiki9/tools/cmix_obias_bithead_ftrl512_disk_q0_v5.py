#!/usr/bin/env python3
"""Build and run one frozen 250KB FTRL512 v5 diagnostic arm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

import cmix_obias_source_1m_roundtrip_qm2 as qualified
import cmix_obias_disk_scratch as disk_scratch


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "programs" / "cmix_obias_bithead_ftrl512_ppm0_q0_v5"
OVERLAY = PROGRAM / "overlay.py"
ARMS = {"C": 0, "P": 0, "K": 1, "O": 2, "R": 3, "D": 4, "S": 5}
RAW_SCOPE = 250_000
OPENING_SHA256 = "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"
MAX_PROGRAM_BYTES = 557_019
RSS_LIMIT_KIB = 9_765_625


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def refuse_concurrent_cmix() -> None:
    offenders: list[dict[str, object]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        if not argv:
            continue
        executable = Path(argv[0]).name
        if executable in {"cmix", "archive9"}:
            offenders.append({"pid": int(entry.name), "argv": argv})
    if offenders:
        raise RuntimeError(f"refusing concurrent CMIX execution: {offenders}")


def process_tree_rss_kib(root_pid: int) -> tuple[int, int, list[int]]:
    rows: dict[int, tuple[int, int]] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            values: dict[str, int] = {}
            for line in (entry / "status").read_text().splitlines():
                if line.startswith("PPid:"):
                    values["ppid"] = int(line.split()[1])
                elif line.startswith("VmRSS:"):
                    values["rss"] = int(line.split()[1])
            rows[int(entry.name)] = (values.get("ppid", 0), values.get("rss", 0))
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
    members = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, (ppid, _) in rows.items():
            if ppid in members and pid not in members:
                members.add(pid)
                changed = True
    rss_values = [rows.get(pid, (0, 0))[1] for pid in members]
    return sum(rss_values), max(rss_values, default=0), sorted(members)


def monitored_command(
    command_args: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None,
    failure_directory: Path,
) -> dict[str, object]:
    started = time.monotonic()
    peak_tree = 0
    peak_single = 0
    peak_members: list[int] = []
    violation: dict[str, object] | None = None
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            command_args,
            cwd=cwd,
            env=environment,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
        )
        while process.poll() is None:
            tree, single, members = process_tree_rss_kib(process.pid)
            if tree > peak_tree:
                peak_tree = tree
                peak_members = members
            peak_single = max(peak_single, single)
            if tree > RSS_LIMIT_KIB:
                violation = {
                    "observed_tree_rss_kib": tree,
                    "limit_kib": RSS_LIMIT_KIB,
                    "members": members,
                }
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                break
            time.sleep(0.25)
        returncode = process.wait()
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read()
        stderr = stderr_file.read()
    receipt: dict[str, object] = {
        "command": command_args,
        "cwd": str(cwd),
        "environment": environment,
        "elapsed_seconds_diagnostic": time.monotonic() - started,
        "returncode": returncode,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout_tail": stdout[-4096:].decode("utf-8", "replace"),
        "stderr_tail": stderr[-4096:].decode("utf-8", "replace"),
        "resource": {
            "peak_process_tree_rss_kib": peak_tree,
            "peak_single_process_rss_kib": peak_single,
            "peak_members": peak_members,
            "limit_kib": RSS_LIMIT_KIB,
            "within_limit": violation is None,
            "violation": violation,
        },
    }
    if violation is not None or returncode != 0:
        failure_directory.mkdir(parents=True, exist_ok=True)
        failure_path = failure_directory / "terminal_stage_failure.json"
        temporary = failure_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        temporary.replace(failure_path)
        raise RuntimeError(
            f"monitored stage failed: returncode={returncode}, violation={violation}"
        )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument(
        "--ppm-always-purge",
        action="store_true",
        required=True,
        help="required sealed PPM budget-zero residency policy for disk v5",
    )
    args = parser.parse_args()
    arm = args.arm
    refuse_concurrent_cmix()

    qm1 = qualified.parent
    qm0 = qm1.parent
    scratch_boundary = disk_scratch.bind_qm0(qm0)
    candidate_id = (
        f"cmix_obias_bithead_ftrl512_ppm0_disk_{arm.lower()}_q0_v5"
    )
    result = ROOT / "results" / candidate_id
    original_command = qm1.command

    def command(
        command_args: list[str],
        *,
        cwd: Path,
        environment: dict[str, str] | None = None,
    ) -> dict[str, object]:
        adjusted = list(command_args)
        if adjusted[:2] == ["make", "prof_use"]:
            adjusted[1] = "cmix"
        executable = Path(adjusted[0]).name if adjusted else ""
        if executable in {"cmix", "cmix_orig", "archive9"}:
            receipt = monitored_command(
                adjusted,
                cwd=cwd,
                environment=environment,
                failure_directory=result,
            )
        else:
            receipt = original_command(adjusted, cwd=cwd, environment=environment)
        if (
            arm != "C"
            and adjusted
            and adjusted[0] == "tar"
            and "-xf" in adjusted
            and "-C" in adjusted
        ):
            source = Path(adjusted[adjusted.index("-C") + 1])
            completed = subprocess.run(
                [sys.executable, str(OVERLAY), "--source", str(source)],
                cwd=cwd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            receipt["gamma_overlay"] = {
                "command": [sys.executable, str(OVERLAY), "--source", str(source)],
                "overlay_sha256": sha256(OVERLAY),
                "returncode": completed.returncode,
                "stdout": completed.stdout.decode("utf-8", "replace").strip(),
                "stderr": completed.stderr.decode("utf-8", "replace").strip(),
            }
        return receipt

    qualified.CANDIDATE_ID = candidate_id
    qualified.RESULT = result
    qm1.command = command
    qm0.RAW_SCOPE = RAW_SCOPE
    qm0.MAX_PROGRAM_BYTES = MAX_PROGRAM_BYTES
    qm0.EXPECTED["opening"] = OPENING_SHA256
    qm0.DEFINES = (
        "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
        "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f "
        f"-DKH_BITHEAD_FTRL_ARM={ARMS[arm]}"
        + (
            " -DCMIX_PPMD_RSS_BUDGET_MB=0ULL"
            if args.ppm_always_purge
            else ""
        )
    )
    returncode = qualified.main()
    if returncode != 0:
        return returncode

    decision_path = result / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision.update(
        {
            "schema": "gamma.enwiki9.cmix-obias-bithead-ftrl512-ppm0-disk-q0-v5",
            "candidate_id": candidate_id,
            "status": "TERMINAL_250KB_DIAGNOSTIC",
            "score_credit_bytes": 0,
            "claim_boundary": (
                "Opening-250KB compile-time arm diagnostic under a non-PGO "
                "matched build. It is not distant transfer, full-corpus evidence, "
                "or a prize score."
            ),
            "gamma_overlay": {
                "arm": arm,
                "arm_value": ARMS[arm],
                "applied": arm != "C",
                "overlay_path": str(OVERLAY.relative_to(ROOT)),
                "overlay_sha256": sha256(OVERLAY) if arm != "C" else None,
                "upstream_bit_head_sha256": (
                    "e0593d64bef9323467d838724f926bb32efdcaef957afd48a14ff318577ff77f"
                ),
                "build_profile": "non_pgo_matched_diagnostic",
                "ppm_always_purge": args.ppm_always_purge,
                "ppm_compile_define": (
                    "-DCMIX_PPMD_RSS_BUDGET_MB=0ULL"
                    if args.ppm_always_purge
                    else None
                ),
                "scratch_boundary": scratch_boundary,
            },
            "population": {"raw_bytes": RAW_SCOPE, "sha256": OPENING_SHA256},
            "decision": {
                "promotion_authorized": False,
                "reason": "Joint P/K/O/R/D/S comparison and receipt audit required.",
                "target_bytes": 105_000_000,
            },
        }
    )
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "event": "delta_midas_arm_terminal",
                "arm": arm,
                "ppm_always_purge": args.ppm_always_purge,
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
