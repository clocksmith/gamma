#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import time


def _children_of(pid: int) -> list[int]:
    path = pathlib.Path("/proc") / str(pid) / "task" / str(pid) / "children"
    try:
        text = path.read_text().strip()
    except OSError:
        return []
    if not text:
        return []
    out = []
    for part in text.split():
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out


def _proc_tree(root: int) -> list[int]:
    seen: set[int] = set()
    stack = [root]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        stack.extend(_children_of(pid))
    return sorted(seen)


def _rss_kib(pid: int) -> int | None:
    path = pathlib.Path("/proc") / str(pid) / "status"
    try:
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith("VmRSS:"):
                fields = line.split()
                if len(fields) >= 2:
                    return int(fields[1])
    except OSError:
        return None
    return None


def _sample(root: int) -> dict:
    processes = []
    max_single = 0
    total = 0
    for pid in _proc_tree(root):
        rss = _rss_kib(pid)
        if rss is None:
            continue
        total += rss
        max_single = max(max_single, rss)
        processes.append({"pid": pid, "rss_kib": rss})
    return {
        "processes": processes,
        "max_single_rss_kib": max_single,
        "tree_rss_kib": total,
    }


def _write_json(path: pathlib.Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-kib", type=int, required=True)
    parser.add_argument("--sample-interval", type=float, default=5.0)
    parser.add_argument("--guard-json", type=pathlib.Path)
    parser.add_argument("--label", default=None)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("missing command after --")

    started_at = time.time()
    proc = subprocess.Popen(command, preexec_fn=os.setsid)
    peak_single = 0
    peak_tree = 0
    peak_sample: dict | None = None
    exceeded = False

    try:
        while True:
            rc = proc.poll()
            sample = _sample(proc.pid)
            if sample["max_single_rss_kib"] > peak_single:
                peak_single = sample["max_single_rss_kib"]
                peak_sample = sample
            peak_tree = max(peak_tree, sample["tree_rss_kib"])
            if sample["max_single_rss_kib"] > args.limit_kib:
                exceeded = True
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                break
            if rc is not None:
                break
            time.sleep(max(args.sample_interval, 0.1))
    finally:
        rc = proc.poll()
        if rc is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            rc = proc.wait()

    payload = {
        "label": args.label,
        "command": command,
        "limit_kib": args.limit_kib,
        "max_sampled_single_rss_kib": peak_single,
        "max_sampled_tree_rss_kib": peak_tree,
        "peak_sample": peak_sample,
        "rss_guard_exceeded": exceeded,
        "returncode": rc,
        "elapsed_s": round(time.time() - started_at, 4),
    }
    _write_json(args.guard_json, payload)
    print(json.dumps({"rss_guard": payload}, indent=2))
    if exceeded:
        return 75
    return int(rc or 0)


if __name__ == "__main__":
    sys.exit(main())
