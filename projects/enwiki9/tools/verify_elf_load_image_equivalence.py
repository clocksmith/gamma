#!/usr/bin/env python3
"""Verify ELI-1 plus LZMA package transcoding for one cmix package."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import lzma
import pathlib
import struct

ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")


def projection(data: bytes) -> dict[str, object]:
    if len(data) < ELF_HEADER.size:
        raise ValueError("truncated ELF header")
    fields = ELF_HEADER.unpack_from(data)
    ident = fields[0]
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1:
        raise ValueError("expected ELF64 little-endian input")
    (
        _,
        elf_type,
        machine,
        version,
        entry,
        phoff,
        _shoff,
        flags,
        _ehsize,
        phentsize,
        phnum,
        _shentsize,
        _shnum,
        _shstrndx,
    ) = fields
    if phentsize != PROGRAM_HEADER.size:
        raise ValueError("unexpected program-header size")
    end = phoff + phnum * phentsize
    if end > len(data):
        raise ValueError("truncated program-header table")
    segments = []
    for index in range(phnum):
        row = PROGRAM_HEADER.unpack_from(data, phoff + index * phentsize)
        (
            kind,
            segment_flags,
            offset,
            virtual_address,
            physical_address,
            file_size,
            memory_size,
            alignment,
        ) = row
        if offset + file_size > len(data):
            raise ValueError("segment payload exceeds file")
        payload = data[offset : offset + file_size]
        segments.append(
            {
                "type": kind,
                "flags": segment_flags,
                "virtual_address": virtual_address,
                "physical_address": physical_address,
                "file_size": file_size,
                "memory_size": memory_size,
                "alignment": alignment,
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return {
        "ident": ident.hex(),
        "type": elf_type,
        "machine": machine,
        "version": version,
        "entry": entry,
        "flags": flags,
        "program_header_size": phentsize,
        "program_header_count": phnum,
        "segments": segments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-binary", type=pathlib.Path, required=True)
    parser.add_argument("--new-binary", type=pathlib.Path, required=True)
    parser.add_argument("--old-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--new-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--old-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--new-wrapper", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    old_binary = gzip.decompress(args.old_binary.read_bytes())
    new_binary = lzma.decompress(args.new_binary.read_bytes())
    old_projection = projection(old_binary)
    new_projection = projection(new_binary)
    if old_projection != new_projection:
        raise AssertionError("ELF loader projections differ")

    old_dictionary = gzip.decompress(args.old_dictionary.read_bytes())
    new_dictionary = lzma.decompress(args.new_dictionary.read_bytes())
    if old_dictionary != new_dictionary:
        raise AssertionError("dictionary payload differs")

    old_source = args.old_wrapper.read_text()
    expected_source = (
        old_source.replace("import gzip", "import lzma")
        .replace("cmix.bin.gz", "cmix.bin.lzma")
        .replace("english.dic.gz", "english.dic.lzma")
        .replace("gzip.open", "lzma.open")
    )
    if args.new_wrapper.read_text() != expected_source:
        raise AssertionError("wrapper edit exceeds frozen ELI-1 grammar")

    old_package = sum(
        path.stat().st_size
        for path in (args.old_binary, args.old_dictionary, args.old_wrapper)
    )
    new_package = sum(
        path.stat().st_size
        for path in (args.new_binary, args.new_dictionary, args.new_wrapper)
    )
    receipt = {
        "schema": "elf_load_image_equivalence_receipt_v1",
        "loader_projection_sha256": hashlib.sha256(
            json.dumps(old_projection, sort_keys=True).encode()
        ).hexdigest(),
        "program_headers": old_projection["program_header_count"],
        "old_binary_bytes": len(old_binary),
        "new_binary_bytes": len(new_binary),
        "dictionary_identity": {
            "bytes": len(old_dictionary),
            "sha256": hashlib.sha256(old_dictionary).hexdigest(),
        },
        "wrapper_grammar_match": True,
        "old_package_bytes": old_package,
        "new_package_bytes": new_package,
        "exact_conditional_score_delta_bytes": new_package - old_package,
        "archive_identity_theorem_applies": True,
        "native_identity": "unmeasured",
        "resource_eligibility": "unmeasured",
        "score_credit_bytes": 0,
        "verdict": "pass",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

