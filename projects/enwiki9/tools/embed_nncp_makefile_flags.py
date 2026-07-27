#!/usr/bin/env python3
"""Embed frozen NNCP CFLAGS in existing Makefile tar slack."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path
import tarfile


FLAGS = (
    b'-O3 -Wall -Wpointer-arith -fno-math-errno -fno-trapping-math -MMD '
    b'-Wno-format-truncation -DCONFIG_VERSION=\\"2024-06-05\\" '
    b'-DLIBNC_CONFIG_FULL'
)
MARKER = b"\n#G=" + FLAGS + b"\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-xz", required=True, type=Path)
    parser.add_argument("--output-tar", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    parent_packed = args.input_xz.read_bytes()
    parent = bytearray(lzma.decompress(parent_packed))
    with tarfile.open(fileobj=io.BytesIO(parent), mode="r:") as archive:
        member = archive.getmember("Makefile")
        old_data = archive.extractfile(member).read()
        member_names = [item.name for item in archive.getmembers()]

    if MARKER.strip() in old_data:
        raise ValueError("carrier marker already exists")
    block_bytes = ((member.size + 511) // 512) * 512
    new_data = old_data + MARKER
    if len(new_data) > block_bytes:
        raise ValueError("literal does not fit existing tar slack")

    child = bytearray(parent)
    child[member.offset_data : member.offset_data + block_bytes] = (
        new_data + b"\0" * (block_bytes - len(new_data))
    )
    header = bytearray(child[member.offset : member.offset + 512])
    header[124:136] = ("%011o\0" % len(new_data)).encode()
    header[148:156] = b"        "
    header[148:156] = ("%06o\0 " % sum(header)).encode()
    child[member.offset : member.offset + 512] = header

    with tarfile.open(fileobj=io.BytesIO(child), mode="r:") as archive:
        restored = archive.extractfile("Makefile").read()
        child_names = [item.name for item in archive.getmembers()]
    if restored != new_data or child_names != member_names:
        raise AssertionError("modified tar failed exact structural verification")

    allowed = set(range(member.offset, member.offset + 512))
    allowed.update(range(member.offset_data, member.offset_data + block_bytes))
    outside_changes = sum(
        left != right
        for index, (left, right) in enumerate(zip(parent, child))
        if index not in allowed
    )
    if outside_changes:
        raise AssertionError("bytes changed outside carrier allocation")

    args.output_tar.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_tar.write_bytes(child)
    receipt = {
        "carrier_member": "Makefile",
        "carrier_offset": member.offset_data,
        "child_makefile_bytes": len(new_data),
        "child_tar_bytes": len(child),
        "child_tar_sha256": sha256(child),
        "flags_bytes": len(FLAGS),
        "flags_sha256": sha256(FLAGS),
        "marker_bytes": len(MARKER),
        "member_block_bytes": block_bytes,
        "outside_carrier_changed_bytes": outside_changes,
        "parent_makefile_bytes": member.size,
        "parent_tar_bytes": len(parent),
        "parent_tar_sha256": sha256(parent),
        "remaining_slack_bytes": block_bytes - len(new_data),
        "schema": "nncp_makefile_slack_embedding_v1",
        "score_credit_bytes": 0,
        "tar_length_preserved": len(parent) == len(child),
        "tar_structure_preserved": True,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
