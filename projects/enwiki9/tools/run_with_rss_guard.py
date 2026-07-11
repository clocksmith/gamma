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
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-kib", type=int, required=True)
    parser.add_argument(
        "--limit-mode",
        choices=("max_single", "tree"),
        default="max_single",
        help="enforce the largest process RSS or aggregate process-tree RSS",
    )
    parser.add_argument("--official-decimal-limit-kib", type=int)
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
    latest_sample: dict | None = None
    sample_count = 0
    exceeded = False
    official_decimal_exceeded = False
    failure: str | None = None

    try:
        while True:
            rc = proc.poll()
            sample = _sample(proc.pid)
            latest_sample = sample
            sample_count += 1
            if sample["max_single_rss_kib"] > peak_single:
                peak_single = sample["max_single_rss_kib"]
                peak_sample = sample
            peak_tree = max(peak_tree, sample["tree_rss_kib"])
            _write_json(
                args.guard_json,
                {
                    "label": args.label,
                    "command": command,
                    "limit_kib": args.limit_kib,
                    "limit_mode": args.limit_mode,
                    "official_decimal_limit_kib": args.official_decimal_limit_kib,
                    "official_decimal_over_limit_kib": (
                        max(0, sample["max_single_rss_kib"] - args.official_decimal_limit_kib)
                        if args.official_decimal_limit_kib is not None
                        else None
                    ),
                    "max_sampled_single_rss_kib": peak_single,
                    "max_sampled_tree_rss_kib": peak_tree,
                    "peak_sample": peak_sample,
                    "latest_sample": sample,
                    "sample_count": sample_count,
                    "rss_guard_exceeded": False,
                    "returncode": None,
                    "status": "running",
                    "elapsed_s": round(time.time() - started_at, 4),
                },
            )
            measured_kib = (
                sample["tree_rss_kib"]
                if args.limit_mode == "tree"
                else sample["max_single_rss_kib"]
            )
            if measured_kib > args.limit_kib:
                exceeded = True
                failure = "compression_rss_crossed_local_guard_before_archive_or_roundtrip"
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
            if (
                args.official_decimal_limit_kib is not None
                and sample["max_single_rss_kib"] > args.official_decimal_limit_kib
            ):
                official_decimal_exceeded = True
                failure = "active_compressor_exceeded_official_decimal_10gb_limit"
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
        "limit_mode": args.limit_mode,
        "official_decimal_limit_kib": args.official_decimal_limit_kib,
        "official_decimal_over_limit_kib": (
            max(0, peak_single - args.official_decimal_limit_kib)
            if args.official_decimal_limit_kib is not None
            else None
        ),
        "max_sampled_single_rss_kib": peak_single,
        "max_sampled_tree_rss_kib": peak_tree,
        "peak_sample": peak_sample,
        "latest_sample": latest_sample,
        "sample_count": sample_count,
        "rss_guard_exceeded": exceeded,
        "returncode": rc,
        "status": (
            "rss_guard_exceeded"
            if exceeded
            else "aborted_official_decimal_memory_limit"
            if official_decimal_exceeded
            else "complete"
        ),
        "elapsed_s": round(time.time() - started_at, 4),
    }
    if failure is not None:
        payload["failure"] = failure
    _write_json(args.guard_json, payload)
    print(json.dumps({"rss_guard": payload}, indent=2))
    if exceeded or official_decimal_exceeded:
        return 75
    return int(rc or 0)


if __name__ == "__main__":
    sys.exit(main())
