#!/usr/bin/env python3
"""Parse fixed CMIX allocation markers into a diagnostic-only receipt."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import struct
from typing import Any


SCHEMA = "gamma.enwiki9.cmix-allocation-marker-receipt.v1"
MAGIC = 0x434F4C4C414D4147
VERSION = 1
RECORD = struct.Struct("<QHHIIIQQQQII")
EVENTS = {1: "allocation", 2: "release", 3: "pageout"}
LABELS = {
    1: "fxcm_alloc",
    2: "fxcm_alloc_aligned",
    10: "context_history",
    11: "context_shared_map",
    12: "context_indirect_1",
    13: "context_indirect_2",
    14: "context_indirect_3",
    20: "mixer_slab",
    30: "ppmd_arena_anonymous",
    31: "ppmd_arena_file_backed",
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def parse(path: Path, source_manifest: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("marker stream must be a regular nonsymlink file")
    if source_manifest.is_symlink() or not source_manifest.is_file():
        raise ValueError("source manifest must be a regular nonsymlink file")
    size = path.stat().st_size
    if size == 0 or size % RECORD.size != 0:
        raise ValueError("marker stream is empty or truncated")

    event_digest = hashlib.sha256()
    live: dict[int, dict[str, Any]] = {}
    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {"allocation_count": 0, "release_count": 0, "pageout_count": 0, "allocated_bytes": 0}
    )
    events = []
    with path.open("rb") as stream:
        for expected_sequence in range(size // RECORD.size):
            raw = stream.read(RECORD.size)
            fields = RECORD.unpack(raw)
            (
                magic,
                version,
                record_bytes,
                sequence,
                event_id,
                label_id,
                allocation_base,
                usable_pointer,
                allocation_bytes,
                usable_bytes,
                alignment,
                reserved,
            ) = fields
            if magic != MAGIC or version != VERSION or record_bytes != RECORD.size:
                raise ValueError(f"record {expected_sequence} header mismatch")
            if sequence != expected_sequence:
                raise ValueError(
                    f"record sequence mismatch: expected {expected_sequence}, observed {sequence}"
                )
            if event_id not in EVENTS or label_id not in LABELS:
                raise ValueError(f"record {sequence} uses unknown event or label")
            if reserved != 0:
                raise ValueError(f"record {sequence} reserved field is nonzero")
            if allocation_base == 0 or usable_pointer < allocation_base:
                raise ValueError(f"record {sequence} pointer geometry is invalid")
            offset = usable_pointer - allocation_base
            if allocation_bytes == 0 or offset > allocation_bytes:
                raise ValueError(f"record {sequence} allocation geometry is invalid")
            if usable_bytes > allocation_bytes - offset:
                raise ValueError(f"record {sequence} usable range escapes allocation")
            if not is_power_of_two(alignment) or usable_pointer % alignment != 0:
                raise ValueError(f"record {sequence} alignment is invalid")

            label = LABELS[label_id]
            event = EVENTS[event_id]
            row = {
                "sequence": sequence,
                "event": event,
                "label": label,
                "allocation_base": allocation_base,
                "usable_pointer": usable_pointer,
                "allocation_bytes": allocation_bytes,
                "usable_bytes": usable_bytes,
                "alignment": alignment,
            }
            event_digest.update(canonical(row))
            events.append(row)
            if event == "allocation":
                if allocation_base in live:
                    raise ValueError(f"record {sequence} duplicates a live allocation base")
                live[allocation_base] = row
                summary[label]["allocation_count"] += 1
                summary[label]["allocated_bytes"] += allocation_bytes
            else:
                allocation = live.get(allocation_base)
                if allocation is None:
                    raise ValueError(f"record {sequence} references a non-live mapping")
                for key in ("label", "usable_pointer", "allocation_bytes", "usable_bytes", "alignment"):
                    if row[key] != allocation[key]:
                        raise ValueError(f"record {sequence} differs from its allocation: {key}")
                if event == "release":
                    del live[allocation_base]
                    summary[label]["release_count"] += 1
                else:
                    summary[label]["pageout_count"] += 1

    return {
        "schema": SCHEMA,
        "candidate_id": "cmix_obias_memory_allocation_markers_q0_v1",
        "authority": "diagnostic_only",
        "marker_stream": {
            "path": str(path.resolve()),
            "bytes": size,
            "sha256": sha256(path),
            "record_bytes": RECORD.size,
            "record_count": len(events),
            "canonical_events_sha256": event_digest.hexdigest(),
        },
        "source_integration_manifest": {
            "path": str(source_manifest.resolve()),
            "bytes": source_manifest.stat().st_size,
            "sha256": sha256(source_manifest),
        },
        "events": events,
        "label_summary": [
            {"label": label, **summary[label]}
            for label in sorted(summary)
        ],
        "live_at_stream_terminal": [
            live[base] for base in sorted(live)
        ],
        "integrity": {
            "complete_fixed_records_pass": True,
            "strict_sequence_pass": True,
            "known_labels_and_events_pass": True,
            "pointer_geometry_pass": True,
            "lifetime_order_pass": True,
        },
        "terminal_pass": True,
        "memory_qualification_authority": False,
        "compression_credit_bytes": 0,
        "score_credit_bytes": 0,
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError("receipt parent must be an existing nonsymlink directory")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical(value))
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marker-stream", required=True)
    parser.add_argument("--source-integration-manifest", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = parse(
        Path(args.marker_stream),
        Path(args.source_integration_manifest),
    )
    write_new(Path(args.receipt), receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
