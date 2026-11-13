#!/usr/bin/env python3
"""Wait for completed9B evidence and cooperative exclusive GPU timing admission.

No service changes or GPU recovery. All run outputs use a new attempt directory.
The lock excludes cooperating lock users; it does not prove global isolation.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def completion(schedule_path):
    result = subprocess.run(["node", str(HERE / "probe_completion_gate.mjs"), str(schedule_path)],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def guard_observation(config):
    try:
        guard = json.loads(Path(config["serviceGuardPath"]).read_text())
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(guard["checkedAt"].replace("Z", "+00:00"))).total_seconds()
        ready = (guard.get("allowed") is True and type(guard.get("stageAdmitted")) is int and guard["stageAdmitted"] == 0
                 and guard.get("providerState") == "inactive" and guard.get("providerSubState") == "dead"
                 and type(guard.get("providerMainPID")) is int and guard["providerMainPID"] == 0 and 0 <= age <= config["serviceGuardMaxAgeMs"] / 1000)
        return {"ready": ready, "ageSeconds": age, "guard": guard}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"ready": False, "reason": type(error).__name__ + ": " + str(error)}


def acquire_exclusive(path):
    # Existing shared9B holder may still be closing after writing its receipt.
    handle = open(path, "a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle
    except BaseException:
        handle.close()
        raise


def validate_plan(schedule, config, lock):
    raw = Path(schedule["protocol"]).read_bytes()
    protocol = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != lock["inputHashes"]["protocol"]:
        raise ValueError("Probe protocol is not the frozen runtime-lock input")
    if hashlib.sha256(Path(schedule["config"]).read_bytes()).hexdigest() != lock["inputHashes"]["config"]:
        raise ValueError("Probe configuration is not the frozen runtime-lock input")
    if schedule["confirmationContract"] != protocol["executionPrerequisite"]:
        raise ValueError("Schedule confirmation gate differs from frozen protocol")
    if schedule["timingContext"] != config["executionContext"] or schedule["timingContext"] != protocol["timing"]:
        raise ValueError("Schedule timing context differs from protocol/config")
    for name in ("run_deferred_probe.py", "probe_completion_gate.mjs", "probe-schedule.json"):
        path = HERE / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != lock["sources"].get("screen/" + name):
            raise ValueError("Deferred wrapper/schedule source changed after probe freeze: " + name)


def run(schedule_path, attempt):
    schedule_path = Path(schedule_path).resolve()
    schedule = json.loads(schedule_path.read_text())
    if schedule_path != (HERE / "probe-schedule.json"):
        raise ValueError("Use the explicitly frozen probe-schedule.json")
    config = json.loads(Path(schedule["config"]).read_text())
    lock = json.loads(Path(schedule["runtimeLock"]).read_text())
    validate_plan(schedule, config, lock)
    attempt = Path(attempt).resolve()
    attempt.mkdir(parents=False, exist_ok=False)
    journal = open(attempt / "scheduler.jsonl", "x", buffering=1)
    child = None
    held = None

    def emit(kind, **fields):
        journal.write(json.dumps({"at": utc(), "kind": kind, **fields}, sort_keys=True) + "\n")

    def interrupted(signum, frame):
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signum)
        else:
            raise KeyboardInterrupt("Scheduler interrupted before model execution")

    previous = {s: signal.signal(s, interrupted) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        emit("scheduler-start", scheduleSha256=hashlib.sha256(schedule_path.read_bytes()).hexdigest(),
             probeLockSha256=lock["lockSha256"], timingContext=schedule["timingContext"], globalIsolationQualified=False)
        while True:
            evidence = completion(schedule_path)
            if not evidence["ready"]:
                emit("waiting-for-confirmation", evidence=evidence)
                time.sleep(schedule["pollSeconds"])
                continue
            guard = guard_observation(config)
            if not guard["ready"]:
                emit("waiting-for-service-guard", observation=guard)
                time.sleep(schedule["pollSeconds"])
                continue
            emit("waiting-for-exclusive-timing-lock", path=schedule["timingLockPath"], confirmation=evidence)
            held = acquire_exclusive(schedule["timingLockPath"])
            emit("exclusive-timing-lock-acquired", path=schedule["timingLockPath"], globalIsolationQualified=False)
            after = completion(schedule_path)
            guard = guard_observation(config)
            if after == evidence and guard["ready"]:
                break
            held.close()
            held = None
            emit("admission-recheck-held", confirmation=after, guard=guard)
            time.sleep(schedule["pollSeconds"])
        args = ["node", str(HERE / "probe.mjs"), "--action", "run", "--gpu-authorized"]
        for key, flag in (("protocol", "protocol"), ("config", "config"), ("tokenizerPreflight", "tokenizer-preflight"),
                          ("corpus", "corpus"), ("runtimeLock", "runtime-lock")):
            args.extend(["--" + flag, schedule[key]])
        args.extend(["--output", str(attempt / "probe-output"), "--timing-lock-fd", str(held.fileno())])
        emit("probe-launch", command=args, confirmation=evidence, guard=guard, globalIsolationQualified=False)
        with open(attempt / "probe-stdout.log", "xb") as output:
            # Inherit the same flock description so parent loss cannot release it
            # while its own Node probe is still running.
            child = subprocess.Popen(args, cwd=schedule["workingDirectory"], stdout=output, stderr=subprocess.STDOUT,
                                     pass_fds=(held.fileno(),), start_new_session=True)
            emit("probe-process-started", pid=child.pid)
            code = child.wait()
        emit("probe-process-ended", pid=child.pid, exitCode=code)
        return code
    except BaseException as error:
        if child is not None and child.poll() is None:
            # Stop only this wrapper's child on coordinator failure; never reset
            # a GPU or touch another owner's process/service.
            os.killpg(child.pid, signal.SIGTERM)
            child.wait()
        emit("scheduler-error", error=type(error).__name__ + ": " + str(error), probeStarted=child is not None)
        raise
    finally:
        if held is not None:
            held.close()
            emit("exclusive-timing-lock-released")
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        journal.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--gpu-authorized", action="store_true")
    args = parser.parse_args()
    if not args.gpu_authorized:
        parser.error("Root launch admission requires --gpu-authorized")
    raise SystemExit(run(args.schedule, args.attempt_dir))
