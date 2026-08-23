#!/usr/bin/env python3
"""Passive CMIX memory phase-attribution evidence collector.

This tool never launches, signals, migrates, or modifies a measured process. Its
receipts are diagnostic only. Resource qualification requires a later clean,
uninstrumented guarded run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import time
from pathlib import Path
from typing import Any, BinaryIO, Iterable


SCHEMA = "gamma.enwiki9.cmix-memory-phase-attribution-observer.v1"
ERROR_SCHEMA = "gamma.enwiki9.cmix-memory-phase-attribution-observer-error.v1"
GAMMA_LIMIT_BYTES = 10_000_000_000
ENGINEERING_TARGET_BYTES = 9_216_000_000
PHASES = {
    "process_start",
    "preprocessing",
    "dictionary_or_order_construction",
    "model_initialization",
    "encode_steady_state",
    "encode_termination_or_archive_construction",
    "decode_initialization",
    "decode_steady_state",
    "raw_reconstruction",
    "cleanup",
    "process_terminal",
    "unknown",
}
EVENTS = {"begin", "checkpoint", "end"}
REQUIRED_MARKER_FIELDS = {
    "sequence",
    "monotonic_nanoseconds",
    "pid",
    "proc_start_ticks",
    "phase",
    "event",
    "payload_sha256",
}
SHA256_KEYS = {
    "integer_probability_stream_sha256",
    "payload_sha256",
    "archive_sha256",
    "inverse_sha256",
    "persistent_state_manifest_sha256",
}


class EvidenceError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("ascii")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(fd)
    try:
        return json.loads(b"".join(chunks))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"invalid JSON input {path}: {exc}") from exc


def write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise EvidenceError("short write")
        offset += written


def create_new_bytes(path: Path, data: bytes, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, mode)
    try:
        write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def create_new_json(path: Path, value: Any) -> None:
    create_new_bytes(path, canonical_bytes(value))


def is_beneath(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def require_regular_nonsymlink(path: Path) -> None:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise EvidenceError(f"expected regular non-symlink file: {path}")


def require_directory_nonsymlink(path: Path) -> None:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise EvidenceError(f"expected directory non-symlink: {path}")


def require_output_path(output_root: Path, path: Path) -> Path:
    root = output_root.resolve(strict=True)
    parent = path.parent.resolve(strict=True)
    resolved = parent / path.name
    if not is_beneath(root, resolved):
        raise EvidenceError(f"output escapes output root: {path}")
    if path.exists() or path.is_symlink():
        raise EvidenceError(f"output already exists: {path}")
    return resolved


def read_text_file(path: Path, maximum: int = 16 * 1024 * 1024) -> bytes:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        result = bytearray()
        while True:
            chunk = os.read(fd, min(1024 * 1024, maximum + 1 - len(result)))
            if not chunk:
                break
            result.extend(chunk)
            if len(result) > maximum:
                raise EvidenceError(f"input exceeds bound: {path}")
        return bytes(result)
    finally:
        os.close(fd)


def parse_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EvidenceError(f"{label} must be a positive integer")
    return value


def nested_value(value: dict[str, Any], paths: Iterable[tuple[str, ...]]) -> Any:
    for keys in paths:
        current: Any = value
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                break
            current = current[key]
        else:
            return current
    return None


def proc_stat(pid: int) -> dict[str, Any] | None:
    path = Path(f"/proc/{pid}/stat")
    try:
        raw = read_text_file(path, 64 * 1024).decode("ascii")
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    right = raw.rfind(")")
    left = raw.find("(")
    if left <= 0 or right <= left:
        raise EvidenceError(f"malformed proc stat for PID {pid}")
    fields = raw[right + 2 :].split()
    if len(fields) < 20:
        raise EvidenceError(f"short proc stat for PID {pid}")
    return {
        "pid": pid,
        "comm": raw[left + 1 : right],
        "state": fields[0],
        "ppid": int(fields[1]),
        "proc_start_ticks": int(fields[19]),
    }


def proc_identity_matches(pid: int, start_ticks: int) -> bool:
    observed = proc_stat(pid)
    return observed is not None and observed["proc_start_ticks"] == start_ticks


def parse_proc_status(pid: int) -> dict[str, int]:
    raw = read_text_file(Path(f"/proc/{pid}/status"), 1024 * 1024).decode(
        "ascii", errors="strict"
    )
    result: dict[str, int] = {}
    byte_fields = {"VmRSS", "VmHWM", "VmSize"}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, text = line.split(":", 1)
        parts = text.split()
        if key in byte_fields:
            if len(parts) != 2 or parts[1] != "kB":
                raise EvidenceError(f"unexpected {key} units for PID {pid}")
            result[key] = int(parts[0]) * 1024
        elif key == "Threads":
            if len(parts) != 1:
                raise EvidenceError(f"unexpected Threads value for PID {pid}")
            result[key] = int(parts[0])
    for key in ("VmRSS", "VmHWM", "VmSize", "Threads"):
        if key not in result:
            raise EvidenceError(f"missing {key} for PID {pid}")
    return result


def command_sha256(pid: int) -> str:
    return sha256_bytes(read_text_file(Path(f"/proc/{pid}/cmdline"), 4 * 1024 * 1024))


def read_smaps_rollup(pid: int) -> dict[str, Any]:
    path = Path(f"/proc/{pid}/smaps_rollup")
    raw = read_text_file(path, 4 * 1024 * 1024)
    values: dict[str, int] = {}
    for line in raw.decode("ascii", errors="strict").splitlines():
        if ":" not in line:
            continue
        key, text = line.split(":", 1)
        parts = text.split()
        if len(parts) == 2 and parts[1] == "kB" and parts[0].isdigit():
            values[key] = int(parts[0]) * 1024
    return {"sha256": sha256_bytes(raw), "values_bytes": values}


def read_maps(pid: int) -> dict[str, Any]:
    raw = read_text_file(Path(f"/proc/{pid}/maps"), 64 * 1024 * 1024)
    mappings: list[dict[str, Any]] = []
    for line in raw.decode("utf-8", errors="surrogateescape").splitlines():
        parts = line.split(None, 5)
        if len(parts) < 5:
            raise EvidenceError(f"malformed maps line for PID {pid}")
        mapping = {
            "address_range": parts[0],
            "permissions": parts[1],
            "offset": parts[2],
            "device": parts[3],
            "inode": parts[4],
            "path": parts[5] if len(parts) == 6 else null_value(),
        }
        mappings.append(mapping)
    return {"sha256": sha256_bytes(raw), "mappings": mappings}


def null_value() -> None:
    return None


def read_process_sample(pid: int) -> dict[str, Any] | None:
    identity = proc_stat(pid)
    if identity is None:
        return None
    try:
        status = parse_proc_status(pid)
        cmd_hash = command_sha256(pid)
    except (FileNotFoundError, ProcessLookupError):
        return None
    identity["command_sha256"] = cmd_hash
    return {
        "identity": identity,
        "rss_bytes": status["VmRSS"],
        "vmhwm_bytes": status["VmHWM"],
        "vmsize_bytes": status["VmSize"],
        "threads": status["Threads"],
    }


def read_int_file(path: Path) -> int | None:
    try:
        text = read_text_file(path, 4096).decode("ascii").strip()
    except FileNotFoundError:
        return None
    if text == "max":
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise EvidenceError(f"invalid integer in {path}") from exc


def read_key_value_file(path: Path) -> tuple[dict[str, int], str] | tuple[None, None]:
    try:
        raw = read_text_file(path, 4 * 1024 * 1024)
    except FileNotFoundError:
        return None, None
    result: dict[str, int] = {}
    for line in raw.decode("ascii", errors="strict").splitlines():
        parts = line.split()
        if len(parts) != 2:
            raise EvidenceError(f"malformed key/value line in {path}")
        result[parts[0]] = int(parts[1])
    return result, sha256_bytes(raw)


def read_cgroup_pids(cgroup: Path) -> list[int]:
    raw = read_text_file(cgroup / "cgroup.procs", 16 * 1024 * 1024)
    result: list[int] = []
    for line in raw.decode("ascii", errors="strict").splitlines():
        if line:
            result.append(int(line))
    return sorted(set(result))


def read_cgroup_snapshot(cgroup: Path) -> dict[str, Any]:
    events, events_hash = read_key_value_file(cgroup / "memory.events")
    memory_stat, memory_stat_hash = read_key_value_file(cgroup / "memory.stat")
    return {
        "memory_current_bytes": read_int_file(cgroup / "memory.current"),
        "memory_peak_bytes": read_int_file(cgroup / "memory.peak"),
        "memory_max_bytes": read_int_file(cgroup / "memory.max"),
        "memory_events": events,
        "memory_events_sha256": events_hash,
        "memory_stat": memory_stat,
        "memory_stat_sha256": memory_stat_hash,
    }


def scratch_usage(root: Path, maximum_entries: int) -> dict[str, Any]:
    require_directory_nonsymlink(root)
    root_info = os.lstat(root)
    root_device = root_info.st_dev
    logical = 0
    allocated = 0
    entries = 0
    complete = True
    errors: list[str] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    entries += 1
                    if entries > maximum_entries:
                        complete = False
                        errors.append("maximum_entries_exceeded")
                        stack.clear()
                        break
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        complete = False
                        errors.append(f"stat:{entry.path}:{exc.errno}")
                        continue
                    if stat.S_ISLNK(info.st_mode):
                        continue
                    if info.st_dev != root_device:
                        complete = False
                        errors.append(f"mount_boundary:{entry.path}")
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(Path(entry.path))
                    elif stat.S_ISREG(info.st_mode):
                        logical += info.st_size
                        allocated += info.st_blocks * 512
        except OSError as exc:
            complete = False
            errors.append(f"scandir:{directory}:{exc.errno}")
    return {
        "root": str(root),
        "logical_bytes": logical,
        "allocated_bytes": allocated,
        "entries": entries,
        "complete": complete,
        "errors": sorted(errors),
    }


class JsonlWriter:
    def __init__(self, path: Path):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        self.path = path
        self.fd = os.open(path, flags, 0o600)
        self.count = 0

    def write(self, value: Any, fsync: bool = False) -> None:
        write_all(self.fd, canonical_bytes(value))
        self.count += 1
        if fsync:
            os.fsync(self.fd)

    def close(self) -> None:
        if self.fd >= 0:
            os.fsync(self.fd)
            os.close(self.fd)
            self.fd = -1


class PhaseReader:
    def __init__(self, source: Path, raw_copy: Path):
        require_regular_nonsymlink(source)
        self.source = source
        self.source_fd = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        self.raw_fd = os.open(raw_copy, flags, 0o600)
        self.offset = 0
        self.pending = b""
        self.events: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.last_sequence: int | None = None
        self.last_monotonic: int | None = None
        self.current_phase = "unknown"

    def poll(self) -> int:
        changed = 0
        while True:
            chunk = os.pread(self.source_fd, 1024 * 1024, self.offset)
            if not chunk:
                break
            self.offset += len(chunk)
            write_all(self.raw_fd, chunk)
            self.pending += chunk
            if len(self.pending) > 2 * 1024 * 1024:
                self.errors.append("phase_stream_unterminated_record_exceeds_bound")
                self.pending = b""
                break
            while b"\n" in self.pending:
                line, self.pending = self.pending.split(b"\n", 1)
                changed += self._consume_line(line)
        return changed

    def _consume_line(self, line: bytes) -> int:
        if not line:
            self.errors.append("empty_phase_record")
            return 0
        if len(line) > 1024:
            self.errors.append("phase_record_exceeds_1024_bytes")
            return 0
        try:
            value = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.errors.append("invalid_phase_json")
            return 0
        if not isinstance(value, dict) or set(value) != REQUIRED_MARKER_FIELDS:
            self.errors.append("invalid_phase_fields")
            return 0
        if canonical_bytes(value).rstrip(b"\n") != line:
            self.errors.append("noncanonical_phase_record")
            return 0
        if value["phase"] not in PHASES or value["event"] not in EVENTS:
            self.errors.append("unknown_phase_or_event")
            return 0
        if not isinstance(value["sequence"], int) or value["sequence"] < 0:
            self.errors.append("invalid_phase_sequence")
            return 0
        if self.last_sequence is not None and value["sequence"] != self.last_sequence + 1:
            self.errors.append("noncontiguous_phase_sequence")
            return 0
        monotonic = value["monotonic_nanoseconds"]
        if not isinstance(monotonic, int) or monotonic < 0:
            self.errors.append("invalid_phase_monotonic_time")
            return 0
        if self.last_monotonic is not None and monotonic < self.last_monotonic:
            self.errors.append("phase_clock_regression")
            return 0
        if not isinstance(value["pid"], int) or value["pid"] <= 0:
            self.errors.append("invalid_phase_pid")
            return 0
        if not isinstance(value["proc_start_ticks"], int) or value["proc_start_ticks"] <= 0:
            self.errors.append("invalid_phase_start_ticks")
            return 0
        payload_hash = value["payload_sha256"]
        if not isinstance(payload_hash, str) or len(payload_hash) != 64:
            self.errors.append("invalid_phase_payload_hash")
            return 0
        try:
            int(payload_hash, 16)
        except ValueError:
            self.errors.append("invalid_phase_payload_hash")
            return 0
        self.last_sequence = value["sequence"]
        self.last_monotonic = monotonic
        self.events.append(value)
        if value["event"] in {"begin", "checkpoint"}:
            self.current_phase = value["phase"]
        elif value["event"] == "end" and self.current_phase == value["phase"]:
            self.current_phase = "unknown"
        return 1

    def finish(self) -> None:
        self.poll()
        if self.pending:
            self.errors.append("unterminated_phase_record_at_terminal")
        os.fsync(self.raw_fd)
        os.close(self.raw_fd)
        os.close(self.source_fd)
        self.raw_fd = -1
        self.source_fd = -1


def capture_mappings(processes: list[dict[str, Any]]) -> dict[str, Any]:
    result: list[dict[str, Any]] = []
    errors: list[str] = []
    for process in processes:
        identity = process["identity"]
        pid = identity["pid"]
        if not proc_identity_matches(pid, identity["proc_start_ticks"]):
            errors.append(f"identity_changed:{pid}")
            continue
        try:
            result.append(
                {
                    "identity": identity,
                    "maps": read_maps(pid),
                    "smaps_rollup": read_smaps_rollup(pid),
                }
            )
        except (FileNotFoundError, ProcessLookupError, PermissionError) as exc:
            errors.append(f"mapping_capture:{pid}:{type(exc).__name__}")
    return {"processes": result, "errors": errors, "complete": not errors}


def output_manifest(paths: Iterable[Path]) -> list[dict[str, Any]]:
    result = []
    for path in sorted(paths, key=lambda item: item.name):
        require_regular_nonsymlink(path)
        result.append(
            {
                "name": path.name,
                "size_bytes": os.lstat(path).st_size,
                "sha256": sha256_file(path),
            }
        )
    return result


def cmd_prepare(args: argparse.Namespace) -> int:
    lock_path = Path(args.experiment_lock)
    require_regular_nonsymlink(lock_path)
    lock = load_json(lock_path)
    if not isinstance(lock, dict):
        raise EvidenceError("experiment lock must be a JSON object")
    output_root = Path(args.output_root)
    if output_root.exists() or output_root.is_symlink():
        raise EvidenceError("output root already exists")
    output_root.mkdir(mode=0o700, parents=False)
    require_directory_nonsymlink(output_root)
    receipt_path = require_output_path(output_root, Path(args.receipt))
    receipt = {
        "schema": SCHEMA,
        "mode": "prepare",
        "authority": "diagnostic_only",
        "experiment_lock": {
            "path": str(lock_path),
            "size_bytes": os.lstat(lock_path).st_size,
            "sha256": sha256_file(lock_path),
        },
        "output_root": str(output_root.resolve(strict=True)),
        "cgroup_plan": lock.get("cgroup", lock.get("cgroup_plan")),
        "measurement_contract": lock.get(
            "measurement_contract", lock.get("measurement")
        ),
        "prepared_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "codec_launched": False,
        "process_migrated": False,
        "execution_authorized": False,
    }
    create_new_json(receipt_path, receipt)
    return 0


def observe_config(lock: dict[str, Any]) -> dict[str, int]:
    interval = nested_value(
        lock,
        (
            ("measurement_contract", "sample_interval_nanoseconds"),
            ("measurement", "sample_interval_nanoseconds"),
            ("sample_interval_nanoseconds",),
        ),
    )
    maximum_entries = nested_value(
        lock,
        (
            ("measurement_contract", "scratch_maximum_entries"),
            ("measurement", "scratch_maximum_entries"),
            ("scratch_maximum_entries",),
        ),
    )
    fsync_every = nested_value(
        lock,
        (
            ("measurement_contract", "fsync_every_samples"),
            ("measurement", "fsync_every_samples"),
            ("fsync_every_samples",),
        ),
    )
    return {
        "sample_interval_nanoseconds": parse_positive_int(interval, "sample interval"),
        "scratch_maximum_entries": parse_positive_int(
            maximum_entries, "scratch maximum entries"
        ),
        "fsync_every_samples": parse_positive_int(fsync_every, "fsync interval"),
    }


def cmd_observe(args: argparse.Namespace) -> int:
    lock_path = Path(args.experiment_lock)
    lock = load_json(lock_path)
    if not isinstance(lock, dict):
        raise EvidenceError("experiment lock must be a JSON object")
    config = observe_config(lock)
    root_pid = parse_positive_int(args.root_pid, "root PID")
    root_start = parse_positive_int(args.root_start_ticks, "root start ticks")
    if not proc_identity_matches(root_pid, root_start):
        raise EvidenceError("root process identity does not match before observation")

    cgroup = Path(args.cgroup)
    phase_stream = Path(args.phase_stream)
    scratch = Path(args.scratch)
    output_root = Path(args.output_root)
    require_directory_nonsymlink(cgroup)
    require_regular_nonsymlink(cgroup / "cgroup.procs")
    require_regular_nonsymlink(phase_stream)
    require_directory_nonsymlink(scratch)
    require_directory_nonsymlink(output_root)

    names = {
        "raw_phase": "phase-stream.raw",
        "samples": "samples.jsonl",
        "mappings": "mapping-checkpoints.jsonl",
        "cgroup": "cgroup-snapshots.jsonl",
        "scratch": "scratch-snapshots.jsonl",
        "phase_events": "phase-events.json",
        "lifetimes": "process-lifetimes.json",
        "high_water": "high-water.json",
    }
    paths = {
        key: require_output_path(output_root, output_root / name)
        for key, name in names.items()
    }
    receipt_path = require_output_path(output_root, Path(args.receipt))
    phase_reader = PhaseReader(phase_stream, paths["raw_phase"])
    sample_writer = JsonlWriter(paths["samples"])
    mapping_writer = JsonlWriter(paths["mappings"])
    cgroup_writer = JsonlWriter(paths["cgroup"])
    scratch_writer = JsonlWriter(paths["scratch"])

    sequence = 0
    tree_peak = 0
    tree_peak_phase = "unknown"
    tree_peak_time = 0
    cgroup_peak: int | None = None
    largest_vmhwm = 0
    largest_identity: dict[str, Any] | None = None
    first_crossing: dict[str, Any] | None = None
    lifetimes: dict[str, dict[str, Any]] = {}
    integrity_errors: list[str] = []
    observed_root = False
    previous_phase = "unknown"
    output_paths = list(paths.values())

    try:
        next_sample = time.monotonic_ns()
        while True:
            now = time.monotonic_ns()
            marker_changes = phase_reader.poll()
            phase = phase_reader.current_phase
            pids = read_cgroup_pids(cgroup)
            if os.getpid() in pids:
                raise EvidenceError("observer entered measured cgroup")
            root_alive = proc_identity_matches(root_pid, root_start)
            if root_alive and root_pid not in pids:
                integrity_errors.append("root_alive_outside_bound_cgroup")
            if root_pid in pids:
                observed_root = True

            process_samples: list[dict[str, Any]] = []
            vanished: list[int] = []
            for pid in pids:
                try:
                    process = read_process_sample(pid)
                except (PermissionError, EvidenceError) as exc:
                    integrity_errors.append(f"process_sample:{pid}:{type(exc).__name__}")
                    continue
                if process is None:
                    vanished.append(pid)
                    continue
                process_samples.append(process)

            process_samples.sort(
                key=lambda item: (
                    item["identity"]["pid"],
                    item["identity"]["proc_start_ticks"],
                )
            )
            membership = [item["identity"] for item in process_samples]
            membership_hash = sha256_bytes(canonical_bytes(membership))
            tree_rss = sum(item["rss_bytes"] for item in process_samples)
            tree_vmsize = sum(item["vmsize_bytes"] for item in process_samples)
            tree_threads = sum(item["threads"] for item in process_samples)
            cgroup_snapshot = read_cgroup_snapshot(cgroup)
            scratch_snapshot = scratch_usage(
                scratch, config["scratch_maximum_entries"]
            )

            for process in process_samples:
                identity = process["identity"]
                key = f"{identity['pid']}:{identity['proc_start_ticks']}"
                lifetime = lifetimes.get(key)
                if lifetime is None:
                    lifetime = {
                        "identity": identity,
                        "first_monotonic_nanoseconds": now,
                        "last_monotonic_nanoseconds": now,
                        "first_phase": phase,
                        "last_phase": phase,
                        "maximum_rss_bytes": process["rss_bytes"],
                        "maximum_vmhwm_bytes": process["vmhwm_bytes"],
                        "maximum_vmsize_bytes": process["vmsize_bytes"],
                        "maximum_threads": process["threads"],
                    }
                    lifetimes[key] = lifetime
                else:
                    lifetime["last_monotonic_nanoseconds"] = now
                    lifetime["last_phase"] = phase
                    lifetime["maximum_rss_bytes"] = max(
                        lifetime["maximum_rss_bytes"], process["rss_bytes"]
                    )
                    lifetime["maximum_vmhwm_bytes"] = max(
                        lifetime["maximum_vmhwm_bytes"], process["vmhwm_bytes"]
                    )
                    lifetime["maximum_vmsize_bytes"] = max(
                        lifetime["maximum_vmsize_bytes"], process["vmsize_bytes"]
                    )
                    lifetime["maximum_threads"] = max(
                        lifetime["maximum_threads"], process["threads"]
                    )
                if process["vmhwm_bytes"] > largest_vmhwm:
                    largest_vmhwm = process["vmhwm_bytes"]
                    largest_identity = identity

            cgroup_current = cgroup_snapshot["memory_current_bytes"]
            observed_cgroup_peak = cgroup_snapshot["memory_peak_bytes"]
            if observed_cgroup_peak is not None:
                cgroup_peak = (
                    observed_cgroup_peak
                    if cgroup_peak is None
                    else max(cgroup_peak, observed_cgroup_peak)
                )
            crossing_value = max(
                tree_rss,
                largest_vmhwm,
                cgroup_peak or 0,
                cgroup_current or 0,
            )
            if first_crossing is None and crossing_value > GAMMA_LIMIT_BYTES:
                first_crossing = {
                    "monotonic_nanoseconds": now,
                    "phase": phase,
                    "observed_lower_bound_bytes": crossing_value,
                    "tree_rss_bytes": tree_rss,
                    "largest_process_vmhwm_bytes": largest_vmhwm,
                    "cgroup_memory_current_bytes": cgroup_current,
                    "cgroup_memory_peak_bytes": cgroup_peak,
                }

            new_tree_peak = tree_rss > tree_peak
            if new_tree_peak:
                tree_peak = tree_rss
                tree_peak_phase = phase
                tree_peak_time = now

            sample = {
                "sequence": sequence,
                "monotonic_nanoseconds": now,
                "phase": phase,
                "tree_membership_sha256": membership_hash,
                "processes": process_samples,
                "vanished_pids": vanished,
                "tree_rss_bytes": tree_rss,
                "tree_vmsize_bytes": tree_vmsize,
                "tree_threads": tree_threads,
                "cgroup_memory_current_bytes": cgroup_current,
                "cgroup_memory_peak_bytes": observed_cgroup_peak,
                "scratch_logical_bytes": scratch_snapshot["logical_bytes"],
                "scratch_allocated_bytes": scratch_snapshot["allocated_bytes"],
                "scratch_complete": scratch_snapshot["complete"],
            }
            fsync_now = (sequence + 1) % config["fsync_every_samples"] == 0
            sample_writer.write(sample, fsync_now)
            cgroup_writer.write(
                {
                    "sequence": sequence,
                    "monotonic_nanoseconds": now,
                    "phase": phase,
                    **cgroup_snapshot,
                },
                fsync_now,
            )
            scratch_writer.write(
                {
                    "sequence": sequence,
                    "monotonic_nanoseconds": now,
                    "phase": phase,
                    **scratch_snapshot,
                },
                fsync_now,
            )
            if sequence == 0 or marker_changes or phase != previous_phase or new_tree_peak:
                mapping_writer.write(
                    {
                        "sequence": sequence,
                        "monotonic_nanoseconds": now,
                        "phase": phase,
                        **capture_mappings(process_samples),
                    },
                    fsync_now,
                )
            previous_phase = phase
            sequence += 1

            if observed_root and not root_alive and not pids:
                break
            next_sample += config["sample_interval_nanoseconds"]
            delay = next_sample - time.monotonic_ns()
            if delay > 0:
                time.sleep(delay / 1_000_000_000)
            else:
                skipped = (-delay) // config["sample_interval_nanoseconds"]
                if skipped:
                    integrity_errors.append(f"sampling_deadline_miss:{skipped}")
                    next_sample += skipped * config["sample_interval_nanoseconds"]
    finally:
        phase_reader.finish()
        sample_writer.close()
        mapping_writer.close()
        cgroup_writer.close()
        scratch_writer.close()

    integrity_errors.extend(phase_reader.errors)
    if not observed_root:
        integrity_errors.append("root_never_observed_in_bound_cgroup")
    phase_events = {
        "events": phase_reader.events,
        "errors": phase_reader.errors,
        "complete": not phase_reader.errors,
    }
    create_new_json(paths["phase_events"], phase_events)
    create_new_json(
        paths["lifetimes"],
        {
            "processes": [lifetimes[key] for key in sorted(lifetimes)],
            "complete": not any(error.startswith("process_sample:") for error in integrity_errors),
        },
    )
    authoritative_peak = max(tree_peak, largest_vmhwm, cgroup_peak or 0)
    high_water = {
        "tree_rss_peak_bytes": tree_peak,
        "tree_rss_peak_phase": tree_peak_phase,
        "tree_rss_peak_monotonic_nanoseconds": tree_peak_time,
        "largest_process_vmhwm_bytes": largest_vmhwm,
        "largest_process_identity": largest_identity,
        "cgroup_memory_peak_bytes": cgroup_peak,
        "authoritative_observed_peak_lower_bound_bytes": authoritative_peak,
        "gamma_limit_bytes": GAMMA_LIMIT_BYTES,
        "engineering_target_bytes": ENGINEERING_TARGET_BYTES,
        "gamma_pass": authoritative_peak <= GAMMA_LIMIT_BYTES and not integrity_errors,
        "first_limit_crossing": first_crossing,
    }
    create_new_json(paths["high_water"], high_water)
    receipt = {
        "schema": SCHEMA,
        "mode": "observe",
        "authority": "diagnostic_only",
        "candidate_id": lock.get("candidate_id"),
        "experiment_lock_sha256": sha256_file(lock_path),
        "root_identity": {"pid": root_pid, "proc_start_ticks": root_start},
        "cgroup": str(cgroup),
        "phase_stream": str(phase_stream),
        "scratch": str(scratch),
        "measurement": config,
        "sample_count": sequence,
        "high_water": high_water,
        "integrity_errors": sorted(set(integrity_errors)),
        "receipt_complete": not integrity_errors,
        "instrumented_memory_qualification": False,
        "outputs": output_manifest(output_paths),
    }
    create_new_json(receipt_path, receipt)
    return 0 if not integrity_errors else 2


def identity_pair(manifest: dict[str, Any], key: str) -> dict[str, Any]:
    parent_key = f"{key}_parent"
    child_key = f"{key}_child"
    parent = manifest.get(parent_key)
    child = manifest.get(child_key)
    valid = (
        isinstance(parent, str)
        and isinstance(child, str)
        and len(parent) == 64
        and len(child) == 64
    )
    if valid:
        try:
            int(parent, 16)
            int(child, 16)
        except ValueError:
            valid = False
    return {
        "parent": parent,
        "child": child,
        "present_and_valid": valid,
        "identity_pass": valid and parent == child,
    }


def cmd_compare(args: argparse.Namespace) -> int:
    parent_path = Path(args.parent_receipt)
    child_path = Path(args.child_receipt)
    manifest_path = Path(args.identity_manifest)
    parent = load_json(parent_path)
    child = load_json(child_path)
    manifest = load_json(manifest_path)
    if not all(isinstance(item, dict) for item in (parent, child, manifest)):
        raise EvidenceError("comparison inputs must be JSON objects")
    comparisons = {key: identity_pair(manifest, key) for key in sorted(SHA256_KEYS)}
    all_present = all(value["present_and_valid"] for value in comparisons.values())
    all_equal = all(value["identity_pass"] for value in comparisons.values())
    receipt = {
        "schema": SCHEMA,
        "mode": "compare",
        "authority": "diagnostic_only",
        "parent_receipt_sha256": sha256_file(parent_path),
        "child_receipt_sha256": sha256_file(child_path),
        "identity_manifest_sha256": sha256_file(manifest_path),
        "parent_candidate_id": manifest.get("parent_candidate_id"),
        "child_candidate_id": manifest.get("child_candidate_id"),
        "scope_manifest_sha256": manifest.get("scope_manifest_sha256"),
        "comparisons": comparisons,
        "all_identities_present": all_present,
        "all_identities_equal": all_equal,
        "instrumented_memory_qualification": False,
    }
    create_new_json(Path(args.receipt), receipt)
    return 0 if all_present and all_equal else 2


def cmd_decide(args: argparse.Namespace) -> int:
    observation_path = Path(args.observation_receipt)
    comparison_path = Path(args.comparison_receipt)
    observation = load_json(observation_path)
    comparison = load_json(comparison_path)
    if not isinstance(observation, dict) or not isinstance(comparison, dict):
        raise EvidenceError("decision inputs must be JSON objects")
    high_water = observation.get("high_water")
    if not isinstance(high_water, dict):
        raise EvidenceError("observation receipt lacks high_water")
    peak = high_water.get("authoritative_observed_peak_lower_bound_bytes")
    if isinstance(peak, bool) or not isinstance(peak, int) or peak < 0:
        raise EvidenceError("invalid observed peak")
    receipt_complete = observation.get("receipt_complete") is True
    identity_pass = (
        comparison.get("all_identities_present") is True
        and comparison.get("all_identities_equal") is True
    )
    if not receipt_complete:
        classification = "invalid_receipt"
    elif not identity_pass:
        classification = "identity_mismatch"
    else:
        classification = "unattributed_peak"
    receipt = {
        "schema": SCHEMA,
        "mode": "decide",
        "authority": "diagnostic_only",
        "observation_receipt_sha256": sha256_file(observation_path),
        "comparison_receipt_sha256": sha256_file(comparison_path),
        "receipt_complete": receipt_complete,
        "identity_pass": identity_pass,
        "observed_peak_lower_bound_bytes": peak,
        "gamma_limit_bytes": GAMMA_LIMIT_BYTES,
        "engineering_target_bytes": ENGINEERING_TARGET_BYTES,
        "hard_limit_reduction_required_bytes": max(0, peak - GAMMA_LIMIT_BYTES),
        "engineering_target_reduction_required_bytes": max(
            0, peak - ENGINEERING_TARGET_BYTES
        ),
        "terminal_classification": classification,
        "memory_child_authorized": False,
        "reason": "Allocation-lifetime attribution and an uninstrumented guarded qualification remain independent requirements.",
    }
    create_new_json(Path(args.receipt), receipt)
    return 2


def preserve_failure_receipt(args: argparse.Namespace, error: Exception) -> str | None:
    if getattr(args, "mode", None) != "observe":
        return None
    root = Path(args.output_root)
    if not root.is_dir():
        return None
    path = root / "observer-error.json"
    if path.exists():
        return str(path)
    partial_artifacts = sorted(
        item.name
        for item in root.iterdir()
        if item != path and item.is_file() and not item.is_symlink()
    )
    receipt = {
        "schema": ERROR_SCHEMA,
        "mode": "observe",
        "authority": "diagnostic_only",
        "terminal_classification": "observer_failure",
        "error_type": type(error).__name__,
        "error": str(error),
        "partial_evidence_preserved": True,
        "partial_evidence_root": str(root.resolve()),
        "partial_artifact_paths": partial_artifacts,
        "intended_receipt_path": str(Path(args.receipt).resolve()),
        "root_pid": args.root_pid,
        "root_proc_start_ticks": args.root_start_ticks,
    }
    create_new_json(path, receipt)
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Passive CMIX memory phase-attribution evidence collector"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--experiment-lock", required=True)
    prepare.add_argument("--output-root", required=True)
    prepare.add_argument("--receipt", required=True)
    prepare.set_defaults(handler=cmd_prepare)

    observe = subparsers.add_parser("observe")
    observe.add_argument("--experiment-lock", required=True)
    observe.add_argument("--root-pid", required=True, type=int)
    observe.add_argument("--root-start-ticks", required=True, type=int)
    observe.add_argument("--cgroup", required=True)
    observe.add_argument("--phase-stream", required=True)
    observe.add_argument("--scratch", required=True)
    observe.add_argument("--output-root", required=True)
    observe.add_argument("--receipt", required=True)
    observe.set_defaults(handler=cmd_observe)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--parent-receipt", required=True)
    compare.add_argument("--child-receipt", required=True)
    compare.add_argument("--identity-manifest", required=True)
    compare.add_argument("--receipt", required=True)
    compare.set_defaults(handler=cmd_compare)

    decide = subparsers.add_parser("decide")
    decide.add_argument("--observation-receipt", required=True)
    decide.add_argument("--comparison-receipt", required=True)
    decide.add_argument("--receipt", required=True)
    decide.set_defaults(handler=cmd_decide)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (EvidenceError, FileNotFoundError, FileExistsError, PermissionError, OSError, RuntimeError, ValueError) as exc:
        failure_receipt = None
        try:
            failure_receipt = preserve_failure_receipt(args, exc)
        except (EvidenceError, FileNotFoundError, FileExistsError, PermissionError, OSError, RuntimeError, ValueError):
            failure_receipt = None
        error = {
            "kind": "cmix_memory_phase_attribution_observer_error",
            "receipt_schema": ERROR_SCHEMA,
            "terminal_classification": "observer_failure",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if failure_receipt is not None:
            error["partial_failure_receipt"] = failure_receipt
        sys.stderr.buffer.write(canonical_bytes(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
