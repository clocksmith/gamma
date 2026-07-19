#!/usr/bin/env python3
"""Screen causal URL host-plus-first-path-prefix reuse before a full WikiIR IR.

Later URLs may reference either a decoder-learned ``host/first-segment`` or,
when that is new, the learned host.  The estimate charges an escape opcode and
insertion-order varint identifier for every reference.  It deliberately does
not claim an inverse or backend result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _varint_bytes(value: int) -> int:
    width = 1
    while value >= 128:
        value >>= 7
        width += 1
    return width


def _host_byte(value: int) -> bool:
    return value not in b" \t\r\n\f\v/][<>{}\"|"


def _parts(data: bytes) -> tuple[tuple[bytes, bytes], ...]:
    output: list[tuple[bytes, bytes]] = []
    position = 0
    while position < len(data):
        starts = [value for value in (data.find(b"http://", position), data.find(b"https://", position)) if value >= 0]
        if not starts:
            break
        start = min(starts)
        host_start = start + (8 if data.startswith(b"https://", start) else 7)
        host_end = host_start
        while host_end < len(data) and _host_byte(data[host_end]):
            host_end += 1
        host = data[host_start:host_end]
        prefix_end = host_end
        if host and host_end < len(data) and data[host_end] == ord("/"):
            prefix_end += 1
            while prefix_end < len(data) and _host_byte(data[prefix_end]):
                prefix_end += 1
        prefix = data[host_start:prefix_end] if prefix_end > host_end + 1 else host
        if host:
            output.append((host, prefix))
        position = max(prefix_end, start + 1)
    return tuple(output)


def run(raw: bytes) -> dict[str, Any]:
    hosts: dict[bytes, int] = {}
    prefixes: dict[bytes, int] = {}
    host_only = 0
    hierarchical = 0
    host_refs = 0
    prefix_refs = 0
    for host, prefix in _parts(raw):
        host_id = hosts.get(host)
        prefix_id = prefixes.get(prefix)
        if host_id is not None:
            host_only += len(host) - 2 - _varint_bytes(host_id)
        if prefix_id is not None:
            hierarchical += len(prefix) - 2 - _varint_bytes(prefix_id)
            prefix_refs += 1
        elif host_id is not None:
            hierarchical += len(host) - 2 - _varint_bytes(host_id)
            host_refs += 1
        hosts.setdefault(host, len(hosts))
        prefixes.setdefault(prefix, len(prefixes))
    return {
        "schema": "wikiir_url_prefix_reuse_probe_v1",
        "evidence_level": "nonconstructive_raw_mdl_headroom",
        "claim_boundary": "Raw event-cost estimate only; no inverse, backend, or official-score claim.",
        "urls": len(_parts(raw)),
        "hosts_learned": len(hosts),
        "prefixes_learned": len(prefixes),
        "host_only_raw_delta_bytes": host_only,
        "hierarchical_raw_delta_bytes": hierarchical,
        "incremental_path_prefix_bytes": hierarchical - host_only,
        "host_references": host_refs,
        "prefix_references": prefix_refs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()[: args.scope_bytes]
    if len(raw) != args.scope_bytes:
        raise ValueError("input is shorter than declared scope")
    result = run(raw)
    result["scope_bytes"] = len(raw)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
