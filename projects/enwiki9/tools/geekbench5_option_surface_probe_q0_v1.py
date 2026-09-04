#!/usr/bin/env python3
"""Run a frozen, network-isolated, nonbenchmark Geekbench 5 option probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "gamma.enwiki9.geekbench5-option-surface-probe-plan.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.geekbench5-option-surface-probe-receipt.v1"
EXPECTED_CANDIDATE = "geekbench5_5_5_1_option_surface_probe_q0_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label}: expected single-link regular file: {absolute}")
    return absolute.resolve(strict=True)


def load_json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(regular_file(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected JSON object")
    return value


def verify_file(record: Any, label: str, base: Path | None = None) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label}: malformed binding")
    path = Path(str(record["path"]))
    if not path.is_absolute():
        path = (base or PROJECT) / path
    path = regular_file(path, label)
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label}: binding mismatch")
    return path


def write_new(path: Path, payload: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "output artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def expected_argv(
    plan: dict[str, Any],
    probe: dict[str, Any],
    tools: dict[str, Path],
    binary: Path,
    trace_prefix: Path,
) -> list[str]:
    options = probe.get("options")
    if not isinstance(options, list) or not all(isinstance(value, str) for value in options):
        raise RuntimeError(f"probe {probe.get('id')}: malformed options")
    if options.count("--sysinfo") != 1 or "--cpu" in options or "--compute" in options:
        raise RuntimeError(f"probe {probe.get('id')}: nonbenchmark invariant failed")
    allowed = {"--no-upload", "--save", "--sysinfo", str(plan["save_sentinel"])}
    if any(value not in allowed for value in options):
        raise RuntimeError(f"probe {probe.get('id')}: unexpected option")
    if "--save" in options:
        index = options.index("--save")
        if index + 1 >= len(options) or options[index + 1] != str(plan["save_sentinel"]):
            raise RuntimeError(f"probe {probe.get('id')}: save target mismatch")
    return [
        str(tools["unshare"]),
        "--user",
        "--map-root-user",
        "--net",
        str(tools["strace"]),
        "-ff",
        "-qq",
        "-e",
        "trace=execve,connect",
        "-o",
        str(trace_prefix),
        str(binary),
        *options,
    ]


def execute(argv: list[str], cwd: Path) -> tuple[int, bytes, bytes, bool]:
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr, timed_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    plan_path = args.plan if args.plan.is_absolute() else PROJECT / args.plan
    plan = load_json(plan_path, "probe plan")
    if (
        plan.get("$schema") != PLAN_SCHEMA
        or plan.get("candidate_id") != EXPECTED_CANDIDATE
        or plan.get("execution_authorized") is not True
        or plan.get("benchmark_authorized") is not False
    ):
        raise RuntimeError("probe plan identity or authority mismatch")

    implementation = verify_file(plan["implementation"], "probe implementation")
    if implementation != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this implementation")
    acquisition = verify_file(plan["acquisition"], "acquisition receipt")
    acquisition_value = load_json(acquisition, "acquisition receipt")
    if acquisition_value.get("benchmark_executed") is not False:
        raise RuntimeError("acquisition antecedent unexpectedly claims a benchmark")

    package_root = Path(plan["package_root"])
    if package_root.resolve(strict=True) != package_root:
        raise RuntimeError("package root must be an exact existing directory")
    binary = verify_file(plan["binary"], "Geekbench launcher")
    worker = verify_file(plan["worker"], "Geekbench worker")
    data = verify_file(plan["data"], "Geekbench data")
    if any(path.parent != package_root for path in (binary, worker, data)):
        raise RuntimeError("Geekbench closure is not contained by the bound package root")
    tools = {
        name: verify_file(record, f"tool {name}") for name, record in plan["tools"].items()
    }

    result_root = Path(plan["result_root"])
    if result_root.parent.resolve(strict=True) != Path(plan["result_parent"]):
        raise RuntimeError("result parent binding mismatch")
    if Path(plan["save_sentinel"]).parent != result_root:
        raise RuntimeError("save sentinel escapes result root")
    if result_root.exists():
        raise RuntimeError("result root already exists")

    if args.validate_only:
        print(json.dumps({"candidate_id": EXPECTED_CANDIDATE, "validation_pass": True}, sort_keys=True))
        return 0

    result_root.mkdir(mode=0o700)
    probes: list[dict[str, Any]] = []
    any_score_text = False
    for probe in plan["probes"]:
        probe_id = str(probe["id"])
        trace_prefix = result_root / f"{probe_id}.strace"
        argv = expected_argv(plan, probe, tools, binary, trace_prefix)
        returncode, stdout, stderr, timed_out = execute(argv, package_root)
        stdout_path = result_root / f"{probe_id}.stdout"
        stderr_path = result_root / f"{probe_id}.stderr"
        write_new(stdout_path, stdout)
        write_new(stderr_path, stderr)
        traces = sorted(result_root.glob(f"{probe_id}.strace*"))
        if not traces:
            raise RuntimeError(f"probe {probe_id}: strace emitted no trace")
        trace_records = [artifact(path) for path in traces]
        trace_text = b"\n".join(path.read_bytes() for path in traces).decode(
            "utf-8", errors="replace"
        )
        combined = (stdout + b"\n" + stderr).decode("utf-8", errors="replace")
        score_text = "Single-Core Score" in combined or "Multi-Core Score" in combined
        any_score_text = any_score_text or score_text
        probes.append(
            {
                "id": probe_id,
                "options": probe["options"],
                "argv": argv,
                "argv_sha256": command_sha256(argv),
                "returncode": returncode,
                "timed_out": timed_out,
                "stdout": artifact(stdout_path),
                "stderr": artifact(stderr_path),
                "traces": trace_records,
                "worker_exec_observed": str(worker) in trace_text,
                "connect_syscalls_observed": trace_text.count("connect("),
                "score_text_observed": score_text,
                "unknown_option_text_observed": "unknown option" in combined.lower()
                or "unrecognized option" in combined.lower(),
            }
        )

    sentinel = Path(plan["save_sentinel"])
    receipt = {
        "$schema": RECEIPT_SCHEMA,
        "candidate_id": EXPECTED_CANDIDATE,
        "terminal": True,
        "claim_authority": "none",
        "objective_credit_bytes": 0,
        "plan": artifact(plan_path),
        "implementation": artifact(implementation),
        "acquisition": artifact(acquisition),
        "benchmark_authorized": False,
        "benchmark_score": None,
        "network_namespace_requested": True,
        "environment": {"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        "package": {
            "launcher": artifact(binary),
            "worker": artifact(worker),
            "data": artifact(data),
        },
        "probes": probes,
        "save_sentinel_exists": sentinel.exists(),
        "score_text_observed": any_score_text,
        "nonbenchmark_invariant_pass": not any_score_text
        and all(not probe["timed_out"] for probe in probes),
        "runtime_authority_established": False,
        "calibration_authorized": False,
    }
    receipt_path = result_root / "receipt.json"
    write_new(
        receipt_path,
        json.dumps(receipt, sort_keys=True, indent=2).encode("ascii") + b"\n",
    )
    print(json.dumps(artifact(receipt_path), sort_keys=True))
    return 0 if receipt["nonbenchmark_invariant_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
