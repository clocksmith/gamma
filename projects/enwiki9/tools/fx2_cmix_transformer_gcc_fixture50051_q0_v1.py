#!/usr/bin/env python3
"""Prospective GCC diagnostic on one immutable public profiling fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
ID = "fx2_cmix_transformer_gcc_fixture50051_q0_v1"
RESULT = PROJECT / "results" / ID
AUDIT = PROJECT / "operations/provenance/public_fx2_cmix_transformer_v1.json"
AUDIT_SHA256 = "4e55dc96f722f769dd52dd9e518472f348e923e8c2b706a46ba0d1bbd972ae79"
SOURCE = PROJECT / "external/fx2-cmix-transformer-v1"
GUARD = PROJECT / "tools/run_with_resource_guard_q0_v13.py"
MEMORY_BYTES = 9899999232
DISK_BYTES = 16000000000
SEPARATOR = [8, 8, 37, 172, 101, 39, 5, 8, 8, 8, 8, 37, 172, 104, 39]
FAST = "-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -ffast-math -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections"
BUILD = ["/usr/bin/make", "-j1", "cmix", "CC=/usr/bin/g++",
         "CPPFLAGS_PART-THAT-SHOULD-BE-FAST=" + FAST + " -O3",
         "CPPFLAGS_PART-THAT-CAN-BE-SLOW=" + FAST + " -Os"]


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path: Path, value: object) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def artifact(path: Path) -> dict:
    return {"path": str(path.relative_to(PROJECT)), "bytes": path.stat().st_size,
            "sha256": digest(path)}


def verify() -> dict:
    if digest(AUDIT) != AUDIT_SHA256:
        raise RuntimeError("public source audit identity drift")
    audit = json.loads(AUDIT.read_text())
    for row in audit["build_source_files"]:
        path = SOURCE / row["path"]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise RuntimeError("public source identity drift: " + row["path"])
    return audit


def marker(phase: str, event: str) -> None:
    path = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    with path.open("a") as handle:
        handle.write(json.dumps({"phase": phase, "event": event}) + "\n")


def run_command(name: str, command: list[str], cwd: Path, seconds: int) -> dict:
    marker(name, "start")
    begin = time.monotonic()
    full = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", str(seconds), *command]
    with (RESULT / (name + ".stdout")).open("xb") as stdout, (RESULT / (name + ".stderr")).open("xb") as stderr:
        completed = subprocess.run(full, cwd=cwd, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdout=stdout, stderr=stderr)
    report = {"command": full, "cwd": str(cwd.relative_to(PROJECT)), "returncode": completed.returncode,
              "elapsed_seconds": time.monotonic() - begin, "elapsed_cap_seconds": seconds,
              "timing_authority": "shared-host diagnostic only"}
    write(RESULT / (name + ".execution.json"), report)
    marker(name, "end")
    if completed.returncode:
        raise RuntimeError(name + " failed; no automatic retry")
    return report


def stage() -> int:
    os.sched_setaffinity(0, {2})
    if os.sched_getaffinity(0) != {2}:
        raise RuntimeError("CPU2 affinity did not bind")
    audit = verify()
    work = RESULT / "work"
    work.mkdir(mode=0o700)
    for row in audit["build_source_files"]:
        destination = work / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (SOURCE / row["path"]).open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    decision = {"schema": "gamma.enwiki9.public-fx2-fixture-diagnostic.v1", "candidate_id": ID,
                "status": "running", "scope_bytes": 50051, "scope": "upstream public prof_input/input; not a canonical prefix",
                "objective_credit_bytes": 0, "roundtrip_ok": None, "deterministic_ok": None,
                "mapping_gate_pass": None, "complete_trained_mapping_equivalence": False,
                "larger_gate_authorized": False, "input": artifact(work / "prof_input/input"), "commands": []}
    try:
        decision["commands"].append(run_command("compile", BUILD, work, 600))
        binary = work / "cmix"
        decision["binary"] = artifact(binary)
        dis = subprocess.run(["/usr/bin/objdump", "-d", "--insn-width=16", str(binary)], capture_output=True, text=True, check=True).stdout
        forbidden = [line for line in dis.splitlines() if re.search(r"\b(v?rcpps|v?rcpss|v?rsqrtps|v?rsqrtss)\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ", line)]
        write(RESULT / "instruction-audit.json", {"reciprocal_and_avx2_check_pass": not forbidden, "forbidden_lines": forbidden[:32], "binary": artifact(binary)})
        if forbidden:
            raise RuntimeError("portable instruction guard failed")
        dictionary = work / "dictionary/english.dic"
        weights = work / "models/6m-q4-fp32.tfwc2"
        fixture = work / "prof_input/input"
        stored = work / "fixture.stored"
        decision["commands"].append(run_command("preprocess", [str(binary), "-s", str(dictionary), str(fixture), str(stored)], work, 120))
        storage = stored.read_bytes()
        if storage[:5] != bytes([128, 0, 0, 0, 0]):
            raise RuntimeError("unexpected dictionary storage header")
        payload = storage[5:]
        vocab = sorted(set(payload))
        mapping = {byte: i for i, byte in enumerate(vocab)}
        first_separator_indices = [mapping[byte] for byte in payload[6:21]]
        mapping_pass = len(payload) >= 10000 and len(vocab) == 205 and payload[0] == 1 and payload[5] == 7 and first_separator_indices == SEPARATOR
        mapping_report = {"stored": artifact(stored), "preprocessed_bytes": len(payload), "observed_vocabulary_size": len(vocab),
                          "observed_vocabulary_bytes": vocab, "first_block_type": payload[0], "dictionary_transform_marker": payload[5],
                          "first_separator_indices": first_separator_indices, "required_first_separator_indices": SEPARATOR,
                          "mapping_gate_pass": mapping_pass, "full_trained_mapping_equivalence": False,
                          "scope": "Count and first separator sanity checks only; no fabricated static map."}
        write(RESULT / "vocabulary-gate.json", mapping_report)
        decision["mapping_gate_pass"] = mapping_pass
        if not mapping_pass:
            decision["status"] = "mapping_rejected"
            decision["reason"] = "Public fixture does not satisfy the frozen transformer vocabulary and separator checks; compression was not invoked."
        else:
            archive = work / "fixture.cmix"
            restored = work / "restored"
            replay = work / "replay.cmix"
            decision["commands"].append(run_command("encode", [str(binary), "-c", str(dictionary), str(fixture), str(archive), "--transformer", str(weights)], work, 120))
            decision["commands"].append(run_command("decode", [str(binary), "-d", str(dictionary), str(archive), str(restored), "--transformer", str(weights)], work, 120))
            decision["commands"].append(run_command("reencode", [str(binary), "-c", str(dictionary), str(fixture), str(replay), "--transformer", str(weights)], work, 120))
            decision["roundtrip_ok"] = fixture.read_bytes() == restored.read_bytes()
            decision["deterministic_ok"] = archive.read_bytes() == replay.read_bytes()
            decision["outputs"] = {name: artifact(path) for name, path in [("archive", archive), ("restored", restored), ("replay", replay)]}
            decision["status"] = "passed" if decision["roundtrip_ok"] and decision["deterministic_ok"] else "failed"
    except Exception as exc:
        decision["status"] = "execution_failed"
        decision["error"] = type(exc).__name__ + ": " + str(exc)
    write(RESULT / "stage-decision.json", decision)
    return 0 if decision["status"] in {"passed", "mapping_rejected"} else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--cgroup-path", type=Path)
    args = parser.parse_args()
    audit = verify()
    if args.validate_only:
        print(json.dumps({"source_binding_pass": True, "files": len(audit["build_source_files"]), "no_build_or_codec_execution": True, "build_argv": BUILD}))
        return 0
    if args.stage:
        return stage()
    if args.cgroup_path is None:
        parser.error("--cgroup-path is required for canonical tool execution")
    expected_cgroup = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-fx2-transformer-fixture50051-q0-v1")
    if args.cgroup_path != expected_cgroup:
        raise RuntimeError("cgroup path must equal the prospectively isolated candidate path")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError("canonical executor must materialize an empty result directory")
    phases = RESULT / "phases.jsonl"
    phases.touch(exist_ok=False)
    command = [sys.executable, str(GUARD), "--limit-kib", str(MEMORY_BYTES // 1024), "--official-decimal-limit-kib", str(MEMORY_BYTES // 1024),
               "--cgroup-memory-max-bytes", str(MEMORY_BYTES), "--cgroup-path", str(args.cgroup_path),
               "--temporary-disk-limit-bytes", str(DISK_BYTES), "--scratch-path", str(RESULT), "--phase-marker-path", str(phases),
               "--guard-json", str(RESULT / "guard.json"), "--label", ID, "--max-logical-cpus", "1", "--",
               "/usr/bin/taskset", "-c", "2", "/usr/bin/timeout", "--kill-after=5", "1100", sys.executable, str(Path(__file__).resolve()), "--stage"]
    with (RESULT / "guard.stdout").open("xb") as stdout, (RESULT / "guard.stderr").open("xb") as stderr:
        completed = subprocess.run(command, cwd=PROJECT, stdout=stdout, stderr=stderr, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    stage_path = RESULT / "stage-decision.json"
    decision = json.loads(stage_path.read_text()) if stage_path.is_file() else {"status": "guard_terminated_without_stage_decision", "roundtrip_ok": None, "deterministic_ok": None, "mapping_gate_pass": None}
    decision.update({"schema": "gamma.enwiki9.public-fx2-fixture-diagnostic.v1", "candidate_id": ID, "guard_returncode": completed.returncode,
                     "guard": artifact(RESULT / "guard.json") if (RESULT / "guard.json").is_file() else None,
                     "objective_credit_bytes": 0, "larger_gate_authorized": False, "guard_command": command})
    if completed.returncode:
        decision["status"] = "execution_failed"
    write(RESULT / "decision.json", decision)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
