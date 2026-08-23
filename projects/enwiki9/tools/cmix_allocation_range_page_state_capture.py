#!/usr/bin/env python3
"""Capture conservative page-state evidence for live CMIX allocations.

This attach-only diagnostic requires a candidate-bound managed exclusive lease
with explicit signaling authority. It never launches a codec and emits no
memory or compression decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any


CANDIDATE = "cmix_obias_source_labelled_memory_attribution_q0_v1"
LEASE_SCHEMA = "gamma.enwiki9.exclusive-full1g-lease.v1"
PAGE_STATE_ENCODING = "one byte per fully contained page: bit 0 present, bit 1 swapped, bits 2 through 7 zero"
UINT64_LIMIT = 1 << 64
PAGEMAP_ENTRY_BYTES = 8
PAGEMAP_BATCH_ENTRIES = 131_072
MAX_FREEZE_ROUNDS = 32
STOP_POLL_ROUNDS = 2_000
STOP_POLL_INTERVAL_SECONDS = 0.005
LABELS = {
    "fxcm_alloc",
    "fxcm_aligned_alloc",
    "context_history",
    "context_shared_map",
    "context_indirect_1",
    "context_indirect_2",
    "context_indirect_3",
    "mixer_slab",
    "ppm_anonymous_arena",
    "ppm_file_backed_arena",
}


class CaptureError(Exception):
    pass


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CaptureError(f"JSON root is not an object: {path}")
    return value, raw


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def proc_stat(pid: int) -> tuple[str, int]:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    close = raw.rfind(")")
    if close < 0:
        raise CaptureError(f"malformed /proc/{pid}/stat")
    fields = raw[close + 2 :].split()
    if len(fields) <= 19:
        raise CaptureError(f"short /proc/{pid}/stat")
    return fields[0], int(fields[19])


def proc_children(pid: int) -> list[int]:
    path = Path(f"/proc/{pid}/task/{pid}/children")
    raw = path.read_text(encoding="ascii").strip()
    if not raw:
        return []
    try:
        return [int(value) for value in raw.split()]
    except ValueError as exc:
        raise CaptureError(f"malformed child list for PID {pid}") from exc


def discover_tree(root_pid: int) -> set[int]:
    discovered: set[int] = set()
    pending = [root_pid]
    while pending:
        pid = pending.pop()
        if pid in discovered:
            continue
        proc_stat(pid)
        discovered.add(pid)
        pending.extend(proc_children(pid))
    return discovered


def read_marker_sequence(path: Path) -> int:
    raw = path.read_text(encoding="ascii").strip()
    if not raw or not raw.isascii() or not raw.isdecimal():
        raise CaptureError("marker sequence file is not one nonnegative decimal integer")
    return int(raw)


def read_exact_pagemap(fd: int, offset: int, length: int) -> bytes:
    chunks: list[bytes] = []
    consumed = 0
    while consumed < length:
        chunk = os.pread(fd, length - consumed, offset + consumed)
        if not chunk:
            raise CaptureError("short read from pagemap")
        chunks.append(chunk)
        consumed += len(chunk)
    return b"".join(chunks)


def parse_maps(raw: bytes) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CaptureError("maps is not valid UTF-8") from exc
    for line_number, line in enumerate(text.splitlines(), start=1):
        fields = line.split(maxsplit=5)
        if not fields or "-" not in fields[0]:
            raise CaptureError(f"malformed maps line {line_number}")
        start_text, end_text = fields[0].split("-", 1)
        start = int(start_text, 16)
        end = int(end_text, 16)
        if not (0 <= start < end <= UINT64_LIMIT):
            raise CaptureError(f"invalid maps range on line {line_number}")
        ranges.append((start, end))
    ranges.sort()
    return ranges


def range_is_mapped(start: int, end: int, mappings: list[tuple[int, int]]) -> bool:
    if start == end:
        return True
    cursor = start
    for mapping_start, mapping_end in mappings:
        if mapping_end <= cursor:
            continue
        if mapping_start > cursor:
            return False
        cursor = max(cursor, mapping_end)
        if cursor >= end:
            return True
    return False


def validate_lease(lease: dict[str, Any], target_pid: int, target_start_ticks: int) -> None:
    if lease.get("schema") != LEASE_SCHEMA:
        raise CaptureError("exclusive lease schema mismatch")
    if lease.get("candidate_id") != CANDIDATE:
        raise CaptureError("exclusive lease belongs to another candidate")
    if lease.get("resource_class") != "exclusive_full1g":
        raise CaptureError("exclusive lease resource class mismatch")
    if lease.get("lease_mode") != "managed":
        raise CaptureError("exclusive lease is not managed")
    if lease.get("signal_authority") is not True:
        raise CaptureError("exclusive lease does not authorize signaling")
    if lease.get("codec_pid") != target_pid:
        raise CaptureError("exclusive lease codec PID mismatch")
    if lease.get("codec_proc_start_ticks") != target_start_ticks:
        raise CaptureError("exclusive lease codec start identity mismatch")
    wrapper_pid = lease.get("pid")
    wrapper_start = lease.get("proc_start_ticks")
    if not isinstance(wrapper_pid, int) or not isinstance(wrapper_start, int):
        raise CaptureError("exclusive lease wrapper identity is incomplete")
    _, observed_wrapper_start = proc_stat(wrapper_pid)
    if observed_wrapper_start != wrapper_start:
        raise CaptureError("exclusive lease wrapper identity is stale")
    _, observed_target_start = proc_stat(target_pid)
    if observed_target_start != target_start_ticks:
        raise CaptureError("target process identity is stale")


class PidfdFreeze:
    def __init__(self, root_pid: int) -> None:
        self.root_pid = root_pid
        self.pidfds: dict[int, int] = {}
        self.start_ticks: dict[int, int] = {}
        self.signaled: list[int] = []

    def _open(self, pid: int) -> None:
        if pid in self.pidfds:
            return
        if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
            raise CaptureError("pidfd signaling is unavailable")
        state, start_ticks = proc_stat(pid)
        if state in ("T", "t"):
            raise CaptureError(f"PID {pid} was already stopped")
        fd = os.pidfd_open(pid, 0)
        state_after, start_after = proc_stat(pid)
        if start_after != start_ticks or state_after in ("T", "t"):
            os.close(fd)
            raise CaptureError(f"PID {pid} changed while opening pidfd")
        self.pidfds[pid] = fd
        self.start_ticks[pid] = start_ticks

    def _signal(self, pid: int, sig: signal.Signals) -> None:
        signal.pidfd_send_signal(self.pidfds[pid], sig, None, 0)

    def _wait_all_stopped(self) -> None:
        for _ in range(STOP_POLL_ROUNDS):
            all_stopped = True
            for pid in self.signaled:
                state, start_ticks = proc_stat(pid)
                if start_ticks != self.start_ticks[pid]:
                    raise CaptureError(f"PID {pid} identity changed while stopping")
                if state not in ("T", "t"):
                    all_stopped = False
                    break
            if all_stopped:
                return
            time.sleep(STOP_POLL_INTERVAL_SECONDS)
        raise CaptureError("process tree did not reach a stopped state")

    def stop(self) -> None:
        for _ in range(MAX_FREEZE_ROUNDS):
            tree = discover_tree(self.root_pid)
            for pid in sorted(tree):
                if pid not in self.pidfds:
                    self._open(pid)
                    self._signal(pid, signal.SIGSTOP)
                    self.signaled.append(pid)
            self._wait_all_stopped()
            stable_tree = discover_tree(self.root_pid)
            if stable_tree.issubset(self.pidfds):
                return
        raise CaptureError("process tree did not stabilize while stopping")

    def identities(self) -> list[dict[str, int]]:
        return [
            {"pid": pid, "proc_start_ticks": self.start_ticks[pid]}
            for pid in sorted(self.signaled)
        ]

    def resume(self) -> list[str]:
        errors: list[str] = []
        for pid in reversed(self.signaled):
            try:
                self._signal(pid, signal.SIGCONT)
            except ProcessLookupError:
                errors.append(f"PID {pid} exited before resume")
            except OSError as exc:
                errors.append(f"cannot resume PID {pid}: {exc}")
        resumed = False
        for _ in range(STOP_POLL_ROUNDS):
            all_running = True
            for pid in self.signaled:
                try:
                    state, start_ticks = proc_stat(pid)
                except OSError as exc:
                    errors.append(f"cannot observe PID {pid} after SIGCONT: {exc}")
                    all_running = False
                    break
                if start_ticks != self.start_ticks[pid]:
                    errors.append(f"PID {pid} identity changed after SIGCONT")
                    all_running = False
                    break
                if state in ("T", "t"):
                    all_running = False
                    break
            if all_running:
                resumed = True
                break
            if errors:
                break
            time.sleep(STOP_POLL_INTERVAL_SECONDS)
        if not resumed and not errors:
            errors.append("process tree remained stopped after SIGCONT")
        for pid, fd in self.pidfds.items():
            try:
                os.close(fd)
            except OSError as exc:
                errors.append(f"cannot close pidfd for PID {pid}: {exc}")
        self.pidfds.clear()
        return errors


def prepare_allocations(live_set: dict[str, Any], page_size: int, mappings: list[tuple[int, int]]) -> list[dict[str, Any]]:
    raw_allocations = live_set.get("allocations")
    if not isinstance(raw_allocations, list):
        raise CaptureError("live allocation set allocations is not an array")
    prepared: list[dict[str, Any]] = []
    seen_sequences: set[int] = set()
    page_intervals: list[tuple[int, int, int]] = []
    offset = 0
    previous_sequence = 0
    for index, raw in enumerate(raw_allocations):
        if not isinstance(raw, dict):
            raise CaptureError(f"allocation {index} is not an object")
        sequence = raw.get("allocation_sequence")
        label = raw.get("label")
        allocation_base = raw.get("allocation_base")
        usable_pointer = raw.get("usable_pointer")
        allocation_bytes = raw.get("allocation_bytes")
        usable_bytes = raw.get("usable_bytes")
        alignment = raw.get("alignment")
        eligible = raw.get("eligible_for_memory_successor")
        integer_fields = (sequence, allocation_base, usable_pointer, allocation_bytes, usable_bytes, alignment)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in integer_fields):
            raise CaptureError(f"allocation {index} has invalid integer geometry")
        if sequence <= previous_sequence or sequence in seen_sequences:
            raise CaptureError("allocations are not in strict sequence order")
        previous_sequence = sequence
        seen_sequences.add(sequence)
        if label not in LABELS or not isinstance(eligible, bool):
            raise CaptureError(f"allocation {index} has invalid label or eligibility")
        if allocation_base >= UINT64_LIMIT or usable_pointer >= UINT64_LIMIT:
            raise CaptureError(f"allocation {index} pointer exceeds uint64")
        if allocation_bytes > UINT64_LIMIT - allocation_base or usable_bytes > UINT64_LIMIT - usable_pointer:
            raise CaptureError(f"allocation {index} range overflows uint64")
        allocation_end = allocation_base + allocation_bytes
        usable_end = usable_pointer + usable_bytes
        if usable_pointer < allocation_base or usable_end > allocation_end:
            raise CaptureError(f"allocation {index} usable range escapes allocation")
        if alignment & (alignment - 1):
            raise CaptureError(f"allocation {index} alignment is not a power of two")
        first_page = (usable_pointer + page_size - 1) // page_size
        end_page = usable_end // page_size
        page_count = max(0, end_page - first_page)
        start_address = first_page * page_size
        end_address = end_page * page_size
        mapped = range_is_mapped(start_address, end_address, mappings)
        if page_count and not mapped:
            raise CaptureError(f"allocation {index} fully contained pages are not mapped")
        if page_count:
            page_intervals.append((first_page, end_page, sequence))
        prepared.append({
            "allocation_sequence": sequence,
            "label": label,
            "allocation_base": allocation_base,
            "usable_pointer": usable_pointer,
            "allocation_bytes": allocation_bytes,
            "usable_bytes": usable_bytes,
            "first_fully_contained_page": first_page,
            "fully_contained_pages": page_count,
            "entry_offset": offset,
            "vma_containment_pass": mapped,
            "eligible_for_memory_successor": eligible,
        })
        offset += page_count
    page_intervals.sort()
    for left, right in zip(page_intervals, page_intervals[1:]):
        if right[0] < left[1]:
            raise CaptureError(f"allocation page ranges overlap: {left[2]} and {right[2]}")
    return prepared


def capture_page_states(pagemap_fd: int, allocations: list[dict[str, Any]]) -> bytes:
    output = bytearray()
    for allocation in allocations:
        first_page = allocation["first_fully_contained_page"]
        remaining = allocation["fully_contained_pages"]
        page_cursor = first_page
        while remaining:
            entries = min(remaining, PAGEMAP_BATCH_ENTRIES)
            raw = read_exact_pagemap(
                pagemap_fd,
                page_cursor * PAGEMAP_ENTRY_BYTES,
                entries * PAGEMAP_ENTRY_BYTES,
            )
            for offset in range(0, len(raw), PAGEMAP_ENTRY_BYTES):
                value = int.from_bytes(raw[offset : offset + PAGEMAP_ENTRY_BYTES], "little")
                present = (value >> 63) & 1
                swapped = (value >> 62) & 1
                output.append(present | (swapped << 1))
            page_cursor += entries
            remaining -= entries
    return bytes(output)


def write_exclusive(path: Path, raw: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def capture(args: argparse.Namespace) -> dict[str, Any]:
    lease, _ = load_json(args.lease)
    live_set, live_set_raw = load_json(args.live_set)
    if live_set.get("schema_version") != "cmix-live-allocation-set.v1" or live_set.get("candidate_id") != CANDIDATE:
        raise CaptureError("live allocation set identity mismatch")
    pid = live_set.get("codec_pid")
    start_ticks = live_set.get("codec_proc_start_ticks")
    marker_sequence = live_set.get("marker_sequence")
    if (
        isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid < 1
        or isinstance(start_ticks, bool)
        or not isinstance(start_ticks, int)
        or start_ticks < 1
        or isinstance(marker_sequence, bool)
        or not isinstance(marker_sequence, int)
        or marker_sequence < 0
    ):
        raise CaptureError("live allocation set process or marker identity is invalid")
    if isinstance(args.checkpoint_index, bool) or args.checkpoint_index < 0:
        raise CaptureError("checkpoint index is invalid")
    validate_lease(lease, pid, start_ticks)
    if args.output_dir.exists():
        if not args.output_dir.is_dir() or any(args.output_dir.iterdir()):
            raise CaptureError("output directory exists and is not empty")
    else:
        args.output_dir.mkdir(parents=True)

    freeze = PidfdFreeze(pid)
    stop_started_ns = time.monotonic_ns()
    capture_exception: Exception | None = None
    resume_errors: list[str] = []
    stopped_processes: list[dict[str, int]] = []
    maps_raw = b""
    smaps_raw = b""
    read_one = b""
    read_two = b""
    allocations: list[dict[str, Any]] = []
    try:
        freeze.stop()
        stopped_processes = freeze.identities()
        if read_marker_sequence(args.marker_sequence_file) != marker_sequence:
            raise CaptureError("marker sequence differs from live allocation set before capture")
        _, observed_start = proc_stat(pid)
        if observed_start != start_ticks:
            raise CaptureError("codec identity changed after stop")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if not isinstance(page_size, int) or page_size <= 0:
            raise CaptureError("invalid system page size")
        maps_raw = Path(f"/proc/{pid}/maps").read_bytes()
        smaps_raw = Path(f"/proc/{pid}/smaps").read_bytes()
        mappings = parse_maps(maps_raw)
        allocations = prepare_allocations(live_set, page_size, mappings)
        pagemap_fd = os.open(f"/proc/{pid}/pagemap", os.O_RDONLY | os.O_CLOEXEC)
        try:
            read_one = capture_page_states(pagemap_fd, allocations)
            read_two = capture_page_states(pagemap_fd, allocations)
        finally:
            os.close(pagemap_fd)
        maps_after = Path(f"/proc/{pid}/maps").read_bytes()
        if maps_after != maps_raw:
            raise CaptureError("codec maps changed while stopped")
        if read_marker_sequence(args.marker_sequence_file) != marker_sequence:
            raise CaptureError("marker sequence changed while stopped")
    except Exception as exc:
        capture_exception = exc
    finally:
        resume_errors = freeze.resume()
    stop_duration_ns = time.monotonic_ns() - stop_started_ns
    if resume_errors:
        raise CaptureError("; ".join(resume_errors))
    if capture_exception is not None:
        if isinstance(capture_exception, CaptureError):
            raise capture_exception
        raise CaptureError(str(capture_exception)) from capture_exception

    total_entries = sum(allocation["fully_contained_pages"] for allocation in allocations)
    if len(read_one) != total_entries or len(read_two) != total_entries:
        raise CaptureError("page-state evidence length mismatch")
    read_one_name = "page-state-read-one.bin"
    read_two_name = "page-state-read-two.bin"
    write_exclusive(args.output_dir / read_one_name, read_one)
    write_exclusive(args.output_dir / read_two_name, read_two)
    write_exclusive(args.output_dir / "maps.txt", maps_raw)
    write_exclusive(args.output_dir / "smaps.txt", smaps_raw)
    manifest = {
        "schema_version": "cmix-allocation-range-page-state-manifest.v1",
        "candidate_id": CANDIDATE,
        "codec_pid": pid,
        "codec_proc_start_ticks": start_ticks,
        "attribution_checkpoint_index": args.checkpoint_index,
        "marker_sequence": marker_sequence,
        "page_size_bytes": os.sysconf("SC_PAGE_SIZE"),
        "live_set_sha256": sha256_bytes(live_set_raw),
        "maps_sha256": sha256_bytes(maps_raw),
        "smaps_sha256": sha256_bytes(smaps_raw),
        "encoding": PAGE_STATE_ENCODING,
        "total_page_entries": total_entries,
        "read_one": {
            "basename": read_one_name,
            "bytes": len(read_one),
            "sha256": sha256_bytes(read_one),
        },
        "read_two": {
            "basename": read_two_name,
            "bytes": len(read_two),
            "sha256": sha256_bytes(read_two),
        },
        "stopped_processes": stopped_processes,
        "stop_resume": {
            "method": "pidfd SIGSTOP/SIGCONT",
            "all_stopped": True,
            "all_resumed": True,
            "stop_duration_ns": stop_duration_ns,
        },
        "allocations": allocations,
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    write_exclusive(args.output_dir / "page-state-manifest.json", encoded.encode("utf-8"))
    return {
        "candidate_id": CANDIDATE,
        "manifest": str(args.output_dir / "page-state-manifest.json"),
        "allocation_ranges": len(allocations),
        "page_entries": total_entries,
        "decision_authority": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease", required=True, type=Path)
    parser.add_argument("--live-set", required=True, type=Path)
    parser.add_argument("--marker-sequence-file", required=True, type=Path)
    parser.add_argument("--checkpoint-index", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output = capture(args)
        status = 0
    except (OSError, CaptureError) as exc:
        output = {
            "candidate_id": CANDIDATE,
            "manifest": None,
            "decision_authority": False,
            "error": str(exc),
        }
        status = 1
    sys.stdout.write(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
