#!/usr/bin/env python3
"""Apply a bounded adjacent-prefix code to the frozen cmix21 dictionary."""

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
MAGIC = b"BPD1"
OFFSET = 32
MAX_LCP = 223
DICTIONARY_MEMBER = "cmix21/english.dic"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_dictionary(data: bytes) -> tuple[bytes, dict[str, int | str | bool]]:
    trailing_newline = data.endswith(b"\n")
    words = data.splitlines()
    previous = b""
    output = bytearray(MAGIC)
    output.append(1 if trailing_newline else 0)
    maximum_lcp = 0
    for index, word in enumerate(words):
        lcp = 0
        limit = min(len(previous), len(word))
        while lcp < limit and previous[lcp] == word[lcp]:
            lcp += 1
        if lcp > MAX_LCP:
            raise ValueError(f"record {index}: LCP {lcp} exceeds {MAX_LCP}")
        output.append(OFFSET + lcp)
        output.extend(word[lcp:])
        output.append(ord("\n"))
        previous = word
        maximum_lcp = max(maximum_lcp, lcp)
    encoded = bytes(output)
    receipt: dict[str, int | str | bool] = {
        "dictionary_bytes": len(data),
        "dictionary_sha256": sha256(data),
        "encoded_dictionary_bytes": len(encoded),
        "encoded_dictionary_sha256": sha256(encoded),
        "line_count": len(words),
        "max_lcp": maximum_lcp,
        "trailing_newline": trailing_newline,
    }
    return encoded, receipt


def decode_dictionary(data: bytes) -> bytes:
    if not data.startswith(MAGIC) or len(data) < len(MAGIC) + 1:
        raise ValueError("invalid bounded-prefix dictionary header")
    trailing_newline = data[len(MAGIC)]
    if trailing_newline not in (0, 1):
        raise ValueError("invalid trailing-newline flag")
    previous = b""
    words: list[bytes] = []
    for index, record in enumerate(data[len(MAGIC) + 1 :].splitlines()):
        if not record:
            raise ValueError(f"record {index}: missing prefix byte")
        lcp = record[0] - OFFSET
        if lcp < 0 or lcp > len(previous):
            raise ValueError(f"record {index}: invalid LCP {lcp}")
        previous = previous[:lcp] + record[1:]
        words.append(previous)
    return b"\n".join(words) + (b"\n" if trailing_newline else b"")


def transform_archive(parent_payload: bytes) -> tuple[bytes, dict[str, int | str | bool]]:
    raw_tar = lzma.decompress(parent_payload, format=lzma.FORMAT_RAW, filters=FILTERS)
    output_buffer = io.BytesIO()
    dictionary_receipt: dict[str, int | str | bool] | None = None
    member_count = 0
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as source_tar:
        with tarfile.open(
            fileobj=output_buffer, mode="w", format=tarfile.USTAR_FORMAT
        ) as output_tar:
            for member in source_tar.getmembers():
                member_count += 1
                if not member.isfile():
                    raise ValueError(f"{member.name}: non-file member is unsupported")
                source = source_tar.extractfile(member)
                if source is None:
                    raise ValueError(f"{member.name}: missing member payload")
                data = source.read()
                if member.name == DICTIONARY_MEMBER:
                    original = data
                    data, dictionary_receipt = encode_dictionary(original)
                    if decode_dictionary(data) != original:
                        raise ValueError("dictionary reconstruction mismatch")
                copied = copy.copy(member)
                copied.size = len(data)
                output_tar.addfile(copied, io.BytesIO(data))
    if dictionary_receipt is None:
        raise ValueError(f"missing {DICTIONARY_MEMBER}")

    transformed_tar = output_buffer.getvalue()
    payload = lzma.compress(
        transformed_tar, format=lzma.FORMAT_RAW, filters=FILTERS
    )
    receipt = {
        "schema": "bounded_prefix_dictionary_quotient_screen_v1",
        **dictionary_receipt,
        "decode_identity": True,
        "member_count": member_count,
        "parent_payload_bytes": len(parent_payload),
        "parent_raw_tar_bytes": len(raw_tar),
        "raw_tar_bytes": len(transformed_tar),
        "raw_tar_sha256": sha256(transformed_tar),
        "payload_bytes": len(payload),
        "payload_sha256": sha256(payload),
        "payload_saved_before_wrapper_bytes": len(parent_payload) - len(payload),
        "score_credit_bytes": 0,
    }
    return payload, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    payload, receipt = transform_archive(args.input.read_bytes())
    args.output.write_bytes(payload)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
