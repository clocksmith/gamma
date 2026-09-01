#!/usr/bin/env python3
"""Build a deterministic source-only fixture for the semantic route tape."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def remap(byte: int) -> int:
    if ord("{") <= byte < 127:
        byte += ord("P") - ord("{")
    elif ord("P") <= byte < ord("T"):
        byte -= ord("P") - ord("{")
    elif ord(":") <= byte <= ord("?") or ord("J") <= byte <= ord("O"):
        byte ^= 0x70
    if byte in (ord("X"), ord("`")):
        byte ^= ord("X") ^ ord("`")
    return byte


class Fixture:
    def __init__(self) -> None:
        self.payload = bytearray()
        self.raw = bytearray()

    def literal(self, text: str) -> None:
        encoded = text.encode("ascii")
        self.raw.extend(encoded)
        self.payload.extend(remap(byte) for byte in encoded)

    def word(self, code: bytes, raw_word: bytes) -> None:
        self.payload.extend(code)
        self.raw.extend(raw_word)

    def control(self, code: int) -> None:
        self.payload.append(code)

    def escaped(self, byte: int) -> None:
        self.payload.extend((0x0C, remap(byte)))
        self.raw.append(byte)


def write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    fixture = Fixture()
    fixture.word(b"\x80", b"a")
    fixture.word(b"\xd0\x80", b"a")
    fixture.word(b"\xf0\xd0\x80", b"a")
    fixture.control(0x40)
    fixture.word(b"\x80", b"A")
    fixture.control(0x07)
    fixture.word(b"\x80", b"A")
    fixture.control(0x06)
    fixture.escaped(ord("!"))

    fixture.literal("{{t|k=ab{c|positional|n={{u|z=v}}|tail=end}}")
    fixture.literal("".join("{{d|k=" for _ in range(17)) + "x" + "}}" * 17)
    fixture.literal("{{" + "n" * 96 + "|" + "k" * 96 + "=v}}")
    fixture.literal("{{" + "n" * 97 + "|k=v}}")
    fixture.literal("{{a|" + "k" * 97 + "=v}}")
    fixture.literal("{{e|k=x{")

    raw = bytes(fixture.raw)
    wrt = b"\x07" + len(raw).to_bytes(4, "big") + b"\x07" + bytes(fixture.payload)
    store = b"\x80\0\0\0\0" + wrt
    dictionary = b"a\n" * 3921

    write_exclusive(args.output_dir / "store.bin", store)
    write_exclusive(args.output_dir / "raw.bin", raw)
    write_exclusive(args.output_dir / "dictionary.txt", dictionary)
    metadata = {
        "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-fixture.v3",
        "candidate_id": "endpoint428_semantic_route_tape_q0_v3",
        "store_bytes": len(store),
        "wrt_stream_bytes": len(wrt),
        "raw_bytes": len(raw),
        "dictionary_bytes": len(dictionary),
        "store_sha256": hashlib.sha256(store).hexdigest(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "dictionary_sha256": hashlib.sha256(dictionary).hexdigest(),
        "coverage": [
            "one_two_three_byte_dictionary_codes",
            "capitalized_uppercase_escape_controls",
            "explicit_and_positional_fields",
            "single_possible_delimiter",
            "nested_route_pause_resume",
            "depth_overflow",
            "96_and_97_byte_atoms",
            "terminal_pending_possible_delimiter"
        ],
        "archive_authority": False,
        "score_credit_bytes": 0
    }
    with (args.output_dir / "fixture.json").open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
