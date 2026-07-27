#!/usr/bin/env python3
"""Build the frozen CQQ-1 comment-quotiented SCC source payload."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
import pathlib
import tarfile


FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]


def strip_comments(data: bytes) -> bytes:
    text = data.decode("utf-8")
    output: list[str] = []
    index = 0
    state = "normal"
    quote = ""
    escaped = False
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "normal":
            if char == "R" and following == '"':
                raise ValueError("raw string literal is outside CQQ-1")
            if char == "/" and following == "/":
                output.append(" ")
                index += 2
                state = "line"
                continue
            if char == "/" and following == "*":
                output.append(" ")
                index += 2
                state = "block"
                continue
            if char in ('"', "'"):
                output.append(char)
                quote = char
                escaped = False
                state = "literal"
                index += 1
                continue
            output.append(char)
            index += 1
            continue
        if state == "literal":
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                state = "normal"
            index += 1
            continue
        if state == "line":
            if char == "\\" and following == "\n":
                output.append("\n")
                index += 2
                continue
            if char == "\n":
                output.append("\n")
                state = "normal"
            index += 1
            continue
        if state == "block":
            if char == "*" and following == "/":
                index += 2
                state = "normal"
                continue
            if char == "\n":
                output.append("\n")
            index += 1
            continue
        raise AssertionError(state)
    if state in {"literal", "block"}:
        raise ValueError(f"unterminated {state}")
    return "".join(output).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()

    parent_blob = args.input.read_bytes()
    parent_raw = lzma.decompress(
        parent_blob, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    with tarfile.open(fileobj=io.BytesIO(parent_raw), mode="r:") as archive:
        members = archive.getmembers()
        rows = []
        removed = 0
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ValueError("invalid SCC member")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("missing SCC member body")
            data = source.read()
            quotient = (
                strip_comments(data)
                if path.suffix in {".cpp", ".h"}
                else data
            )
            removed += len(data) - len(quotient)
            rows.append((member.name, quotient))

    buffer = io.BytesIO()
    with tarfile.open(
        fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT
    ) as archive:
        for name, data in rows:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            archive.addfile(member, io.BytesIO(data))
    quotient_raw = buffer.getvalue()
    quotient_blob = lzma.compress(
        quotient_raw, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    if lzma.decompress(
        quotient_blob, format=lzma.FORMAT_RAW, filters=FILTERS
    ) != quotient_raw:
        raise AssertionError("quotient payload roundtrip failed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(quotient_blob)
    digest = lambda value: hashlib.sha256(value).hexdigest()
    receipt = {
        "schema": "cpp_comment_quotient_screen_v1",
        "member_count": len(rows),
        "source_bytes_removed": removed,
        "parent_raw_tar_bytes": len(parent_raw),
        "raw_tar_bytes": len(quotient_raw),
        "parent_payload_bytes": len(parent_blob),
        "payload_bytes": len(quotient_blob),
        "payload_saved_bytes": len(parent_blob) - len(quotient_blob),
        "raw_tar_sha256": digest(quotient_raw),
        "payload_sha256": digest(quotient_blob),
        "roundtrip": True,
        "score_credit_bytes": 0,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
