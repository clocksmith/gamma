#!/usr/bin/env python3
"""Move the frozen B2 build flags into an exact FCF raw-LZMA2 closure."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath


FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
MEMBER = "cmix21/.gamma_lflags"
FLAGS = (
    "-std=c++14 -Wall -O3 "
    "-DCMIX_PAQ8_LEVEL=5 "
    "-DCMIX_PPMD_MEMORY_MB=21 -DCMIX_PPMD_MEMORY_KB=20352 "
    "-DCMIX_PAQ8_MAIN_CONTEXT_SCALE=1 -DCMIX_PAQ8_MAIN_CONTEXT_DIV=1 "
    "-DCMIX_PAQ8_TEXT_MODEL_SCALE=1 -DCMIX_PAQ8_TEXT_MODEL_DIV=1 "
    "-DCMIX_PAQ8_MATCH_SCALE=1 -DCMIX_PAQ8_MATCH_DIV=1 "
    "-DCMIX_PAQ8_SPARSE_MATCH_DIV=8 -DCMIX_PAQ8_RCM_DIV=32 "
    "-DCMIX_PAQ8_BUF_SCALE=1 -DCMIX_PAQ8_BUF_DIV=32 "
    "-DCMIX_FXCM_CMC2_DIV=1 -DCMIX_FXCM_RCM_DIV=20 "
    "-DCMIX_FXCM_MHASH_DIV=1 -DCMIX_FXCM_CMC2_IDX13_DIV=2 "
    "-DCMIX_FXCM_CMC2_ASSOC=10"
).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode(frame: bytes) -> list[tuple[str, bytes]]:
    if frame[:4] != b"FCF1" or len(frame) < 6:
        raise ValueError("invalid FCF frame")
    count = int.from_bytes(frame[4:6], "big")
    cursor = 6
    members: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for _ in range(count):
        if cursor + 6 > len(frame):
            raise ValueError("truncated FCF record")
        name_size = int.from_bytes(frame[cursor : cursor + 2], "big")
        data_size = int.from_bytes(frame[cursor + 2 : cursor + 6], "big")
        cursor += 6
        name_end = cursor + name_size
        data_end = name_end + data_size
        if data_end > len(frame):
            raise ValueError("truncated FCF payload")
        name = frame[cursor:name_end].decode()
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or name in seen:
            raise ValueError("unsafe or duplicate FCF member")
        seen.add(name)
        members.append((name, frame[name_end:data_end]))
        cursor = data_end
    if cursor != len(frame):
        raise ValueError("trailing FCF bytes")
    return members


def encode(members: list[tuple[str, bytes]]) -> bytes:
    output = bytearray(b"FCF1")
    output.extend(len(members).to_bytes(2, "big"))
    for name, payload in members:
        encoded = name.encode()
        output.extend(len(encoded).to_bytes(2, "big"))
        output.extend(len(payload).to_bytes(4, "big"))
        output.extend(encoded)
        output.extend(payload)
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    parent_payload = args.input.read_bytes()
    parent_frame = lzma.decompress(
        parent_payload, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    members = decode(parent_frame)
    if any(name == MEMBER for name, _payload in members):
        raise ValueError("literal member already exists")
    child_members = [*members, (MEMBER, FLAGS)]
    child_frame = encode(child_members)
    if decode(child_frame) != child_members:
        raise AssertionError("child FCF roundtrip failed")
    child_payload = lzma.compress(
        child_frame, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    if lzma.decompress(
        child_payload, format=lzma.FORMAT_RAW, filters=FILTERS
    ) != child_frame:
        raise AssertionError("child LZMA2 roundtrip failed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(child_payload)
    receipt = {
        "child_frame_bytes": len(child_frame),
        "child_frame_sha256": sha256(child_frame),
        "child_member_count": len(child_members),
        "child_payload_bytes": len(child_payload),
        "child_payload_sha256": sha256(child_payload),
        "compressed_growth_bytes": len(child_payload) - len(parent_payload),
        "literal_bytes": len(FLAGS),
        "literal_member": MEMBER,
        "literal_sha256": sha256(FLAGS),
        "parent_frame_bytes": len(parent_frame),
        "parent_frame_sha256": sha256(parent_frame),
        "parent_member_count": len(members),
        "parent_payload_bytes": len(parent_payload),
        "parent_payload_sha256": sha256(parent_payload),
        "roundtrip_ok": True,
        "schema": "literal_migration_fcf_b2_v1",
        "score_credit_bytes": 0,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
