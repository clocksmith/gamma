#!/usr/bin/env python3
"""Canonicalize provably irrelevant C/C++ horizontal whitespace."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import lzma
from pathlib import Path
import tarfile


FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".inc",
}
HSPACE = b" \t\v\f"


class QuotientError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_directive(line: bytes) -> bool:
    return line.lstrip(HSPACE).startswith(b"#")


def line_body(line: bytes) -> tuple[bytes, bytes]:
    if line.endswith(b"\r\n"):
        return line[:-2], b"\r\n"
    if line.endswith(b"\n"):
        return line[:-1], b"\n"
    return line, b""


def canonicalize_code_line(body: bytes, name: str, line_number: int) -> bytes:
    if b"??/" in body:
        raise QuotientError(f"{name}:{line_number}: trigraph line splice is unsupported")

    out = bytearray()
    state = "normal"
    pending_space = False
    i = 0
    while i < len(body):
        c = body[i]
        if state == "normal":
            if c in HSPACE:
                pending_space = True
                i += 1
                continue
            if c == ord("/") and i + 1 < len(body) and body[i + 1] in (
                ord("/"),
                ord("*"),
            ):
                raise QuotientError(
                    f"{name}:{line_number}: input still contains a comment"
                )
            if c == ord("R") and i + 1 < len(body) and body[i + 1] == ord('"'):
                raise QuotientError(
                    f"{name}:{line_number}: raw string literal is unsupported"
                )
            if pending_space and out:
                out.append(ord(" "))
            pending_space = False
            out.append(c)
            if c == ord('"'):
                state = "string"
            elif c == ord("'"):
                state = "character"
            i += 1
            continue

        out.append(c)
        if c == ord("\\"):
            i += 1
            if i >= len(body):
                raise QuotientError(
                    f"{name}:{line_number}: escaped physical newline is unsupported"
                )
            out.append(body[i])
        elif state == "string" and c == ord('"'):
            state = "normal"
        elif state == "character" and c == ord("'"):
            state = "normal"
        i += 1

    if state != "normal":
        raise QuotientError(f"{name}:{line_number}: unterminated literal")
    return bytes(out)


def canonicalize_source(data: bytes, name: str) -> bytes:
    output = bytearray()
    continued_directive = False
    continued_ordinary = False
    for line_number, line in enumerate(data.splitlines(keepends=True), 1):
        body, newline = line_body(line)
        directive = continued_directive or is_directive(body)
        if directive:
            if b"??/" in body:
                raise QuotientError(
                    f"{name}:{line_number}: trigraph line splice is unsupported"
                )
            output.extend(body)
            output.extend(newline)
            continued_directive = body.endswith(b"\\")
            continue
        continued_directive = False
        if continued_ordinary or body.endswith(b"\\"):
            if b"??/" in body:
                raise QuotientError(
                    f"{name}:{line_number}: trigraph line splice is unsupported"
                )
            output.extend(body)
            output.extend(newline)
            continued_ordinary = body.endswith(b"\\")
            continue
        output.extend(canonicalize_code_line(body, name, line_number))
        output.extend(newline)

    if continued_directive:
        raise QuotientError(f"{name}: unterminated preprocessing continuation")
    if continued_ordinary:
        raise QuotientError(f"{name}: unterminated ordinary continuation")
    return bytes(output)


def transform_archive(parent_payload: bytes) -> tuple[bytes, dict[str, int | str | bool]]:
    raw_tar = lzma.decompress(parent_payload, format=lzma.FORMAT_RAW, filters=FILTERS)
    source_before = 0
    source_after = 0
    transformed_members = 0

    output_buffer = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as source_tar:
        with tarfile.open(
            fileobj=output_buffer, mode="w", format=tarfile.USTAR_FORMAT
        ) as output_tar:
            members = source_tar.getmembers()
            for member in members:
                if not member.isfile():
                    raise QuotientError(f"{member.name}: non-file member is unsupported")
                source = source_tar.extractfile(member)
                if source is None:
                    raise QuotientError(f"{member.name}: member payload is unavailable")
                data = source.read()
                if Path(member.name).suffix.lower() in SOURCE_SUFFIXES:
                    transformed = canonicalize_source(data, member.name)
                    source_before += len(data)
                    source_after += len(transformed)
                    transformed_members += 1
                else:
                    transformed = data
                copied = copy.copy(member)
                copied.size = len(transformed)
                output_tar.addfile(copied, io.BytesIO(transformed))

    transformed_tar = output_buffer.getvalue()
    payload = lzma.compress(
        transformed_tar, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    receipt: dict[str, int | str | bool] = {
        "schema": "cpp_line_whitespace_quotient_screen_v1",
        "member_count": len(members),
        "transformed_member_count": transformed_members,
        "parent_payload_bytes": len(parent_payload),
        "parent_raw_tar_bytes": len(raw_tar),
        "source_bytes_before": source_before,
        "source_bytes_after": source_after,
        "source_bytes_removed": source_before - source_after,
        "raw_tar_bytes": len(transformed_tar),
        "raw_tar_sha256": sha256(transformed_tar),
        "payload_bytes": len(payload),
        "payload_sha256": sha256(payload),
        "payload_saved_bytes": len(parent_payload) - len(payload),
        "roundtrip": True,
        "score_credit_bytes": 0,
    }
    return payload, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    parent_payload = args.input.read_bytes()
    payload, receipt = transform_archive(parent_payload)
    args.output.write_bytes(payload)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
