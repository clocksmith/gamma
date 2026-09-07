#!/usr/bin/env python3
"""Retain bounded synthetic integration attempts in this unique owned tree."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OWNED = Path(__file__).resolve().parent
PLAN = "operations/provenance/fx2_causal_preceding_wrt250k_q0_v1_plan.json"
SOURCES = ["tools/causal_field_preceding_adapter250k_v1.py", "tools/fx2_causal_field_preceding_replay_v1.py",
    "tests/test_fx2_causal_field_preceding_replay_v1.py", "tools/causal_field_preceding_selector_v1.py",
    "tools/causal_field_wrt_adapter_v1.py", "tools/causal_field_dependency_v1.py", "tools/wrt_exact.py",
    "tools/causal_field_parent_coder_v1.py", "tools/fx2_causal_field_replay_v1.py"]
CAPS = {"cpu_set": [4], "address_space_bytes": 536870912, "cpu_seconds": 60,
        "wall_seconds": 120, "file_bytes": 33554432, "scratch_bytes": 33554432}


def info(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def limits():
    os.sched_setaffinity(0, {4})
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(120)


def main():
    attempt = OWNED / sys.argv[1]
    attempt.mkdir(exist_ok=False)
    scratch = attempt / "scratch"
    scratch.mkdir()
    plan = json.loads((ROOT / PLAN).read_bytes())
    for row in plan["sealed_source_inputs"]:
        actual = info(ROOT / row["path"])
        if actual["bytes"] != row["bytes"] or "sha256:" + actual["sha256"] != row["sha256"]:
            write(attempt / "rejected-source.json", {"expected": row, "actual": actual})
            raise ValueError("sealed source changed: " + row["path"])
    paths = sorted(set(SOURCES + [PLAN] + [row["path"] for row in plan["sealed_source_inputs"]]))
    before = [info(ROOT / path) for path in paths]
    for relative in paths:
        target = attempt / "sources" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (attempt / "run.py").write_bytes(Path(__file__).read_bytes())
    command = [sys.executable, "-B", str(ROOT / SOURCES[2])]
    environment = {**os.environ, "TMPDIR": str(scratch), "TMP": str(scratch), "TEMP": str(scratch),
        "GAMMA_PRECEDING_INTEGRATION_RETAIN": str(attempt), "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "PYTHONHASHSEED": "0"}
    write(attempt / "command.json", {"command": command, "cwd": str(ROOT), "caps": CAPS,
        "publication": "6fcb1ff11febc57ff0ec8b0b3e85072fd334fb01", "sources_before": before,
        "environment_overrides": {key: environment[key] for key in
            ("TMPDIR", "TMP", "TEMP", "GAMMA_PRECEDING_INTEGRATION_RETAIN", "PYTHONDONTWRITEBYTECODE",
             "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONHASHSEED")}})
    started = time.monotonic()
    prior = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (attempt / "regression.log").open("wb") as log:
        try:
            process = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                     preexec_fn=limits, timeout=120)
            returncode, error = process.returncode, None
        except subprocess.TimeoutExpired as failure:
            returncode, error = None, str(failure)
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    after = [info(ROOT / path) for path in paths]
    write(attempt / "execution.json", {"schema": "gamma.enwiki9.preceding-integration-synthetic-execution.v1",
        "command": command, "returncode": returncode, "error": error,
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds_including_reaped_children": usage.ru_utime + usage.ru_stime - prior.ru_utime - prior.ru_stime,
        "maximum_child_rss_kib": usage.ru_maxrss, "caps": CAPS, "sources_before": before,
        "sources_after": after, "source_identity_equal": before == after, "corpus_bytes": 0,
        "qualification_authority": False, "complete_package_bytes": None, "full_corpus_score": None})
    rows = [info(path) for path in sorted(attempt.rglob("*")) if path.is_file()]
    write(attempt / "inventory.json", {"files": rows, "indexed_bytes": sum(row["bytes"] for row in rows),
        "self_excluded": str(attempt / "inventory.json")})
    owned_bytes = sum(path.stat().st_size for path in OWNED.rglob("*") if path.is_file())
    if returncode != 0 or before != after or owned_bytes > CAPS["scratch_bytes"]:
        raise SystemExit("synthetic attempt failed; exact artifacts retained at " + str(attempt))
    print(json.dumps({"attempt": str(attempt), "execution": info(attempt / "execution.json"),
                      "inventory": info(attempt / "inventory.json"), "owned_bytes": owned_bytes}))


if __name__ == "__main__":
    main()
