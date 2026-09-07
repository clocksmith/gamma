"""Exact decoder for FX2/CMIX21 WRT text-segment stores.

The parser emits one event only after all stored bytes for that event are
available.  Consumers may therefore replay events causally by releasing an
event at its ``end`` stream offset.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


TEXT_SEGMENT = 7
UPPERCASE = 0x07
END_UPPER = 0x06
CAPITALIZED = 0x40
ESCAPE = 0x0C


def read_dictionary_words(path: Path) -> list[bytes]:
    words: list[bytes] = []
    current = bytearray()
    for value in path.read_bytes():
        if ord("a") <= value <= ord("z"):
            current.append(value)
        elif current:
            words.append(bytes(current))
            current.clear()
    if current:
        words.append(bytes(current))
    return words


def wrt_byte_transform(value: int) -> int:
    """Apply the involution used by FX2's WRT storage wrapper."""
    value &= 0xFF
    if ord("{") <= value < 127:
        value += ord("P") - ord("{")
    elif ord("P") <= value < ord("T"):
        value -= ord("P") - ord("{")
    elif ord(":") <= value <= ord("?") or ord("J") <= value <= ord("O"):
        value ^= 0x70
    if value in (ord("X"), ord("`")):
        value ^= ord("X") ^ ord("`")
    return value & 0xFF


def detect_storage_header(stored: bytes) -> int:
    if len(stored) >= 11 and stored[1:5] == b"\0\0\0\0" and stored[5] == TEXT_SEGMENT:
        return 5
    if len(stored) >= 6 and stored[0] == TEXT_SEGMENT:
        return 0
    raise ValueError("input is neither a full FX2 store nor a bare WRT stream")


def token_index(code: bytes) -> int:
    if len(code) == 1 and 0x80 <= code[0] <= 0xCF:
        return code[0] - 0x80
    if len(code) == 2 and 0xD0 <= code[0] <= 0xFF and 0x80 <= code[1] <= 0xCF:
        return 80 + (code[0] - 0xD0) * 80 + (code[1] - 0x80)
    if (
        len(code) == 3
        and code[0] >= 0xF0
        and 0xD0 <= code[1] <= 0xEF
        and 0x80 <= code[2] <= 0xCF
    ):
        return (
            3920
            + (code[0] - 0xF0) * 32 * 80
            + (code[1] - 0xD0) * 80
            + code[2]
            - 0x80
        )
    raise ValueError(f"invalid WRT dictionary code: {code.hex()}")


@dataclass
class WrtDecoderState:
    uppercase: bool = False
    capitalized: bool = False

    def control(self, value: int) -> None:
        if value == UPPERCASE:
            self.uppercase = True
        elif value == CAPITALIZED:
            self.capitalized = True
        elif value == END_UPPER:
            self.uppercase = False
        else:
            raise ValueError("unsupported WRT control byte")

    def escaped(self, value: int) -> bytes:
        self.uppercase = False
        return bytes((value & 0xFF,))

    def word(self, word: bytes) -> bytes:
        output = bytearray(word)
        for index, value in enumerate(output):
            if index == 0 and self.capitalized:
                output[index] = value - ord("a") + ord("A")
                self.capitalized = False
            if self.uppercase:
                output[index] = output[index] - ord("a") + ord("A")
        return bytes(output)

    def literal(self, value: int) -> bytes:
        is_alpha = ord("a") <= value <= ord("z") or ord("A") <= value <= ord("Z")
        if not is_alpha:
            self.uppercase = False
        if self.capitalized or self.uppercase:
            value = (value - ord("a") + ord("A")) & 0xFF
        if self.capitalized:
            self.capitalized = False
        return bytes((value & 0xFF,))


@dataclass(frozen=True)
class WrtEvent:
    start: int
    end: int
    encoded: bytes
    decoded: bytes
    kind: str

    @property
    def bit_length(self) -> int:
        return 8 * len(self.encoded)


@dataclass(frozen=True)
class ParsedStore:
    stored: bytes
    storage_header_bytes: int
    stream: bytes
    raw_length: int
    events: tuple[WrtEvent, ...]
    decoded: bytes
    kind_counts: dict[str, int]


def parse_store_bytes(stored: bytes, dictionary_words: list[bytes]) -> ParsedStore:
    header_bytes = detect_storage_header(stored)
    stream = stored[header_bytes:]
    if len(stream) < 6 or stream[0] != TEXT_SEGMENT:
        raise ValueError("invalid WRT text segment")
    raw_length = int.from_bytes(stream[1:5], "big")
    if stream[5] != TEXT_SEGMENT:
        raise ValueError("WRT dictionary transform is disabled")
    state = WrtDecoderState()
    decoded = bytearray()
    events: list[WrtEvent] = []
    kinds: Counter[str] = Counter()
    position = 6
    while position < len(stream):
        start = position
        first = wrt_byte_transform(stream[position])
        position += 1
        if first == ESCAPE:
            if position >= len(stream):
                raise ValueError("truncated WRT escape")
            value = wrt_byte_transform(stream[position])
            position += 1
            kind = "escaped_literal"
            output = state.escaped(value)
        elif first in (UPPERCASE, END_UPPER, CAPITALIZED):
            kind = "control"
            state.control(first)
            output = b""
        elif first >= 0x80:
            code = bytearray((first,))
            if first > 0xCF:
                if position >= len(stream):
                    raise ValueError("truncated two-byte WRT token")
                second = wrt_byte_transform(stream[position])
                position += 1
                code.append(second)
                if second > 0xCF:
                    if position >= len(stream):
                        raise ValueError("truncated three-byte WRT token")
                    code.append(wrt_byte_transform(stream[position]))
                    position += 1
            index = token_index(bytes(code))
            if index >= len(dictionary_words):
                raise ValueError("WRT token exceeds dictionary")
            kind = "token"
            output = state.word(dictionary_words[index])
        else:
            kind = "literal"
            output = state.literal(first)
        event = WrtEvent(
            start=start,
            end=position,
            encoded=stream[start:position],
            decoded=output,
            kind=kind,
        )
        events.append(event)
        kinds[kind] += 1
        decoded.extend(output)
    if len(decoded) != raw_length:
        raise ValueError("WRT decoded length differs from segment header")
    return ParsedStore(
        stored=stored,
        storage_header_bytes=header_bytes,
        stream=stream,
        raw_length=raw_length,
        events=tuple(events),
        decoded=bytes(decoded),
        kind_counts=dict(sorted(kinds.items())),
    )


def parse_store(path: Path, dictionary: Path) -> ParsedStore:
    return parse_store_bytes(path.read_bytes(), read_dictionary_words(dictionary))
