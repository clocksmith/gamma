#!/usr/bin/env python3
"""Parse and validate the q1 allocator's fixed 64-byte event stream."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import struct
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-event-receipt.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
MAGIC = 0x31465847
VERSION = 1
RECORD = struct.Struct("<IHHQQQQQQQ")
CADENCE = 1048576
UINT64_MAX = (1 << 64) - 1
MAX_STREAM_BYTES = 384 * 1024 * 1024


def open_stream_without_symlinks(path: Path) -> int:
    raw_path = os.fspath(path)
    if not raw_path or "\x00" in raw_path:
        raise SystemExit("stream path is empty or contains NUL")
    absolute = raw_path.startswith("/")
    components = raw_path.split("/")
    if absolute:
        components = components[1:]
    if not components or any(
        component in {"", ".", ".."} for component in components
    ):
        raise SystemExit("stream path must be lexically canonical")
    directory = os.open(
        "/" if absolute else ".",
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        for component in components[:-1]:
            next_directory = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = next_directory
        descriptor = os.open(
            components[-1],
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=directory,
        )
    finally:
        os.close(directory)
    return descriptor


def read_bound_stream(path: Path) -> tuple[bytes, str]:
    descriptor = open_stream_without_symlinks(path)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise SystemExit("stream must be a regular file")
        if before.st_nlink != 1:
            raise SystemExit("hard-linked event stream is forbidden")
        if before.st_size > MAX_STREAM_BYTES:
            raise SystemExit(
                f"event stream exceeds frozen {MAX_STREAM_BYTES}-byte parser ceiling"
            )
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_STREAM_BYTES:
                raise SystemExit("event stream grew beyond the parser ceiling while reading")
            chunks.append(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after or total != before.st_size:
            raise SystemExit("event stream identity or size changed while reading")
        return b"".join(chunks), digest.hexdigest()
    finally:
        os.close(descriptor)


def open_parent_without_symlinks(path: Path) -> tuple[int, str]:
    raw_path = os.fspath(path)
    if not raw_path or "\x00" in raw_path:
        raise SystemExit("output path is empty or contains NUL")
    absolute = raw_path.startswith("/")
    components = raw_path.split("/")
    if absolute:
        components = components[1:]
    if not components or any(
        component in {"", ".", ".."} for component in components
    ):
        raise SystemExit("output path must be lexically canonical")
    directory = os.open(
        "/" if absolute else ".",
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        for component in components[:-1]:
            next_directory = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = next_directory
        return directory, components[-1]
    except BaseException:
        os.close(directory)
        raise


def write_exclusive_fsynced(path: Path, content: bytes) -> None:
    directory, name = open_parent_without_symlinks(path)
    descriptor = -1
    created = False
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        created = True
        cursor = 0
        while cursor < len(content):
            written = os.write(descriptor, content[cursor:])
            if written <= 0:
                raise OSError("short write while publishing event receipt")
            cursor += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.fsync(directory)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        if created:
            try:
                os.unlink(name, dir_fd=directory)
                os.fsync(directory)
            except OSError:
                pass
        raise
    finally:
        os.close(directory)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    raw, stream_sha256 = read_bound_stream(args.stream)
    complete_records = len(raw) % RECORD.size == 0
    if not complete_records:
        errors.append("event stream has a partial terminal record")
    record_count = len(raw) // RECORD.size

    allocations: list[dict[str, Any]] = []
    allocation_by_id: dict[int, dict[str, Any]] = {}
    live: set[int] = set()
    releases: list[dict[str, Any]] = []
    pageout_cycles: list[dict[str, Any]] = []
    current_cycle: dict[str, Any] | None = None
    saw_pageout = False
    cleanup_sequence: int | None = None
    terminal_modeled_bytes: int | None = None
    strict_sequence = True
    known_types = True
    allocation_geometry = True
    allocation_before_pageout = True
    zero_pageout_return_codes = True
    release_lifecycle = True

    def finalize_cycle() -> None:
        nonlocal current_cycle
        if current_cycle is None:
            return
        observed = [call["mapping_id"] for call in current_cycle["calls"]]
        expected = current_cycle["expected_live_mapping_ids"]
        current_cycle["complete_pass"] = observed == expected
        if not current_cycle["complete_pass"]:
            errors.append(
                f"pageout cycle {current_cycle['cycle']} mappings differ: "
                f"expected={expected} observed={observed}"
            )
        pageout_cycles.append(current_cycle)
        current_cycle = None

    for index in range(record_count):
        fields = RECORD.unpack_from(raw, index * RECORD.size)
        magic, version, event_type, sequence, mapping_id, modeled_bytes, base, usable, mapping_bytes, detail = fields
        if magic != MAGIC:
            errors.append(f"record {index}: bad magic")
        if version != VERSION:
            errors.append(f"record {index}: bad version")
        if sequence != index + 1:
            strict_sequence = False
            errors.append(f"record {index}: expected sequence {index + 1}, got {sequence}")

        if event_type == 1:
            finalize_cycle()
            if saw_pageout:
                allocation_before_pageout = False
                errors.append(f"record {index}: allocation occurred after pageout began")
            alignment = detail >> 48
            requested = detail & 0x0000FFFFFFFFFFFF
            expected_usable = (base + alignment - 1) & ~(alignment - 1) if alignment else 0
            geometry_pass = (
                mapping_id == len(allocations)
                and mapping_id not in allocation_by_id
                and base > 0
                and mapping_bytes >= 67108864
                and requested > 0
                and requested <= mapping_bytes
                and alignment > 0
                and alignment & (alignment - 1) == 0
                and usable == expected_usable
                and usable + requested <= base + mapping_bytes
            )
            if not geometry_pass:
                allocation_geometry = False
                errors.append(f"record {index}: invalid allocation geometry")
            allocation = {
                "sequence": sequence,
                "mapping_id": mapping_id,
                "modeled_bytes": modeled_bytes,
                "mapping_base": base,
                "usable_pointer": usable,
                "mapping_bytes": mapping_bytes,
                "requested_bytes": requested,
                "alignment": alignment,
            }
            allocations.append(allocation)
            allocation_by_id[mapping_id] = allocation
            live.add(mapping_id)
        elif event_type in (2, 3):
            saw_pageout = True
            reason = "post_initialization" if event_type == 2 else "fixed_cadence"
            key = (event_type, modeled_bytes)
            if current_cycle is None or current_cycle["_key"] != key:
                finalize_cycle()
                current_cycle = {
                    "_key": key,
                    "cycle": len(pageout_cycles),
                    "reason": reason,
                    "modeled_bytes": modeled_bytes,
                    "calls": [],
                    "expected_live_mapping_ids": sorted(live),
                    "complete_pass": False,
                }
            result = detail & 0xFFFFFFFF
            if result & 0x80000000:
                result -= 1 << 32
            if result != 0:
                zero_pageout_return_codes = False
                errors.append(f"record {index}: pageout returned {result}")
            current_cycle["calls"].append(
                {
                    "sequence": sequence,
                    "mapping_id": mapping_id,
                    "registry_order": mapping_id,
                    "return_code": result,
                }
            )
            if mapping_id not in live:
                errors.append(f"record {index}: pageout references non-live mapping {mapping_id}")
        elif event_type == 4:
            finalize_cycle()
            if mapping_id not in live:
                release_lifecycle = False
                errors.append(f"record {index}: duplicate or unknown release {mapping_id}")
            else:
                live.remove(mapping_id)
            releases.append(
                {
                    "sequence": sequence,
                    "mapping_id": mapping_id,
                    "modeled_bytes": modeled_bytes,
                }
            )
        elif event_type == 5:
            finalize_cycle()
            if cleanup_sequence is not None:
                errors.append(f"record {index}: duplicate cleanup-complete event")
            cleanup_sequence = sequence
            terminal_modeled_bytes = modeled_bytes
            if mapping_id != UINT64_MAX:
                errors.append(f"record {index}: cleanup mapping id is not UINT64_MAX")
            if index != record_count - 1:
                errors.append(f"record {index}: cleanup-complete event is not last")
        else:
            finalize_cycle()
            known_types = False
            errors.append(f"record {index}: unknown event type {event_type}")

    finalize_cycle()
    for cycle in pageout_cycles:
        cycle.pop("_key", None)

    initial_cycles = [cycle for cycle in pageout_cycles if cycle["reason"] == "post_initialization"]
    initial_cycle_pass = (
        len(initial_cycles) == 1
        and initial_cycles[0]["modeled_bytes"] == 0
        and initial_cycles[0]["complete_pass"]
        and bool(allocations)
    )
    if not initial_cycle_pass:
        errors.append("initial pageout cycle is missing, duplicated, nonzero, or incomplete")

    cadence_cycles = [cycle for cycle in pageout_cycles if cycle["reason"] == "fixed_cadence"]
    observed_modeled = [cycle["modeled_bytes"] for cycle in cadence_cycles]
    expected_cycle_count = (
        terminal_modeled_bytes // CADENCE
        if terminal_modeled_bytes is not None
        else 0
    )
    fixed_cadence_pass = (
        len(observed_modeled) == expected_cycle_count
        and all(
            modeled_bytes == (index + 1) * CADENCE
            for index, modeled_bytes in enumerate(observed_modeled)
        )
    )
    if not fixed_cadence_pass:
        first_mismatch = next(
            (
                index
                for index, modeled_bytes in enumerate(observed_modeled)
                if modeled_bytes != (index + 1) * CADENCE
            ),
            None,
        )
        errors.append(
            "fixed pageout cadence differs: "
            f"expected_count={expected_cycle_count} "
            f"observed_count={len(observed_modeled)} "
            f"first_mismatch_index={first_mismatch}"
        )

    complete_live_cycles = all(cycle["complete_pass"] for cycle in pageout_cycles)
    cleanup_last_pass = cleanup_sequence == record_count and terminal_modeled_bytes is not None
    if not cleanup_last_pass:
        errors.append("cleanup-complete event is missing or nonterminal")
    all_released = not live and len(releases) == len(allocations)
    if not all_released:
        errors.append(f"not all mappings released exactly once: remaining={sorted(live)}")

    integrity = {
        "complete_records_pass": complete_records,
        "strict_sequence_pass": strict_sequence,
        "known_event_types_pass": known_types,
        "allocation_geometry_pass": allocation_geometry,
        "allocation_before_pageout_pass": allocation_before_pageout,
        "initial_cycle_pass": initial_cycle_pass,
        "fixed_cadence_pass": fixed_cadence_pass,
        "complete_live_mapping_cycles_pass": complete_live_cycles,
        "zero_pageout_return_codes_pass": zero_pageout_return_codes,
        "release_lifecycle_pass": release_lifecycle,
        "cleanup_last_pass": cleanup_last_pass,
        "all_mappings_released_pass": all_released,
    }
    terminal_pass = not errors and all(integrity.values())
    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authority": "allocator_event_integrity_only",
        "stream": {
            "path": str(args.stream),
            "bytes": len(raw),
            "sha256": stream_sha256,
            "record_bytes": RECORD.size,
            "record_count": record_count,
            "byte_order": "little",
            "magic_hex": "31465847",
            "version": VERSION,
            "parser_stream_ceiling_bytes": MAX_STREAM_BYTES,
        },
        "allocations": allocations,
        "pageout_cycles": pageout_cycles,
        "releases": releases,
        "terminal_modeled_bytes": terminal_modeled_bytes,
        "integrity": integrity,
        "errors": errors,
        "terminal_pass": terminal_pass,
        "memory_qualification_authority": False,
        "compression_credit_bytes": 0,
        "score_credit_bytes": 0,
    }
    rendered = (json.dumps(output, sort_keys=True, indent=2) + "\n").encode("utf-8")
    write_exclusive_fsynced(args.output, rendered)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
