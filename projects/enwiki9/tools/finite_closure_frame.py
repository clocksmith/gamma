#!/usr/bin/env python3
"""Replace a canonical regular-file USTAR closure with a finite byte frame."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import struct
import tarfile


FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
MAGIC = b"FCF1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_members(members: list[tuple[str, bytes]]) -> bytes:
    if len(members) > 65535:
        raise ValueError("too many closure members")
    output = bytearray(MAGIC)
    output.extend(struct.pack(">H", len(members)))
    seen: set[str] = set()
    for name, data in members:
        path = PurePosixPath(name)
        encoded_name = name.encode("utf-8")
        if (
            not name
            or path.is_absolute()
            or ".." in path.parts
            or name in seen
            or len(encoded_name) > 65535
            or len(data) > 0xFFFFFFFF
        ):
            raise ValueError(f"invalid closure member: {name!r}")
        seen.add(name)
        output.extend(struct.pack(">HI", len(encoded_name), len(data)))
        output.extend(encoded_name)
        output.extend(data)
    return bytes(output)


def decode_members(frame: bytes) -> list[tuple[str, bytes]]:
    if not frame.startswith(MAGIC) or len(frame) < 6:
        raise ValueError("invalid finite closure frame")
    cursor = 4
    count = struct.unpack(">H", frame[cursor : cursor + 2])[0]
    cursor += 2
    members: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for _ in range(count):
        if cursor + 6 > len(frame):
            raise ValueError("truncated closure record")
        name_length, data_length = struct.unpack(
            ">HI", frame[cursor : cursor + 6]
        )
        cursor += 6
        end_name = cursor + name_length
        end_data = end_name + data_length
        if end_data > len(frame):
            raise ValueError("truncated closure payload")
        name = frame[cursor:end_name].decode("utf-8")
        data = frame[end_name:end_data]
        cursor = end_data
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or name in seen:
            raise ValueError(f"unsafe closure member: {name!r}")
        seen.add(name)
        members.append((name, data))
    if cursor != len(frame):
        raise ValueError("trailing closure bytes")
    return members


def transform_payload(parent_payload: bytes) -> tuple[bytes, dict[str, int | str | bool]]:
    raw_tar = lzma.decompress(parent_payload, format=lzma.FORMAT_RAW, filters=FILTERS)
    members: list[tuple[str, bytes]] = []
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                raise ValueError(f"{member.name}: non-file member is unsupported")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"{member.name}: missing member payload")
            members.append((member.name, source.read()))
    frame = encode_members(members)
    if decode_members(frame) != members:
        raise ValueError("finite closure frame reconstruction mismatch")
    payload = lzma.compress(frame, format=lzma.FORMAT_RAW, filters=FILTERS)
    receipt: dict[str, int | str | bool] = {
        "schema": "finite_closure_frame_screen_v1",
        "member_count": len(members),
        "decode_identity": True,
        "parent_raw_tar_bytes": len(raw_tar),
        "frame_bytes": len(frame),
        "frame_saved_raw_bytes": len(raw_tar) - len(frame),
        "frame_sha256": sha256(frame),
        "parent_payload_bytes": len(parent_payload),
        "payload_bytes": len(payload),
        "payload_saved_before_wrapper_bytes": len(parent_payload) - len(payload),
        "payload_sha256": sha256(payload),
        "score_credit_bytes": 0,
    }
    return payload, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    payload, receipt = transform_payload(args.input.read_bytes())
    args.output.write_bytes(payload)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
