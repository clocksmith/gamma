#!/usr/bin/env python3
"""Reversible RADIX-STC N0-N4 numeric-run transforms.

This is an independent implementation of the experiment described in
docs/radix_stc_research_plan.md. It does not copy STC source code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


MAGIC = b"RSTC1\0"
ESC = 0
LONG_RUN = 12
SINGLE_DIGIT = 13
VARIANTS = {"n0": 0, "n1": 1, "n2": 2, "n3": 3, "n4": 4}


class TransformError(ValueError):
    pass


@dataclass
class Slot:
    token_index: int
    length: int
    ordinal: int
    value: bytes = b""


Token = int | Slot


def _uvarint(value: int) -> bytes:
    if value < 0:
        raise TransformError("negative unsigned integer")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _read_uvarint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data) and shift <= 63:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
    raise TransformError("invalid unsigned integer")


def _is_digit(value: int) -> bool:
    return 48 <= value <= 57


def _tokenize(data: bytes, variant: int) -> tuple[list[Token], list[Slot]]:
    tokens: list[Token] = []
    slots: list[Slot] = []
    offset = 0
    while offset < len(data):
        if not _is_digit(data[offset]):
            tokens.append(data[offset])
            offset += 1
            continue
        end = offset + 1
        while end < len(data) and _is_digit(data[end]):
            end += 1
        run = data[offset:end]
        values = (bytes([value]) for value in run) if variant == 1 else (run,)
        for value in values:
            slot = Slot(
                token_index=len(tokens),
                length=len(value),
                ordinal=len(slots),
                value=value,
            )
            tokens.append(slot)
            slots.append(slot)
        offset = end
    return tokens, slots


def _serialize_main(tokens: list[Token], variant: int) -> bytes:
    output = bytearray()
    for token in tokens:
        if isinstance(token, int):
            if token == ESC:
                output.extend((ESC, ESC))
            else:
                output.append(token)
            continue
        if variant == 1:
            output.extend((ESC, SINGLE_DIGIT))
        elif token.length <= 11:
            output.extend((ESC, token.length))
        else:
            output.extend((ESC, LONG_RUN))
            output.extend(_uvarint(token.length - LONG_RUN))
    return bytes(output)


def _parse_main(main: bytes, variant: int) -> tuple[list[Token], list[Slot]]:
    tokens: list[Token] = []
    slots: list[Slot] = []
    offset = 0
    while offset < len(main):
        value = main[offset]
        offset += 1
        if value != ESC:
            tokens.append(value)
            continue
        if offset >= len(main):
            raise TransformError("trailing escape in main component")
        tag = main[offset]
        offset += 1
        if tag == ESC:
            tokens.append(ESC)
            continue
        if tag == SINGLE_DIGIT and variant == 1:
            length = 1
        elif 1 <= tag <= 11 and variant != 1:
            length = tag
        elif tag == LONG_RUN and variant != 1:
            extra, offset = _read_uvarint(main, offset)
            length = LONG_RUN + extra
        else:
            raise TransformError(f"invalid main-component tag {tag}")
        slot = Slot(
            token_index=len(tokens),
            length=length,
            ordinal=len(slots),
        )
        tokens.append(slot)
        slots.append(slot)
    return tokens, slots


def _literal_neighbors(
    tokens: list[Token], token_index: int, direction: int, limit: int = 2
) -> bytes:
    values: list[int] = []
    index = token_index + direction
    while 0 <= index < len(tokens) and len(values) < limit:
        token = tokens[index]
        if isinstance(token, int):
            values.append(token)
        index += direction
    if direction < 0:
        values.reverse()
    return bytes(values)


def _phases(tokens: list[Token]) -> dict[int, int]:
    inside_tag = False
    result: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if isinstance(token, Slot):
            result[index] = int(inside_tag)
        elif token == 60:
            inside_tag = True
        elif token == 62:
            inside_tag = False
    return result


def _ordered_slots(tokens: list[Token], slots: list[Slot], variant: int) -> list[Slot]:
    if variant <= 2:
        return list(slots)
    if variant == 3:
        return sorted(slots, key=lambda slot: (slot.length, slot.ordinal))
    phases = _phases(tokens)
    return sorted(
        slots,
        key=lambda slot: (
            min(slot.length, LONG_RUN),
            slot.length,
            phases[slot.token_index],
            _literal_neighbors(tokens, slot.token_index, -1),
            _literal_neighbors(tokens, slot.token_index, 1),
            slot.ordinal,
        ),
    )


def _pack_digits(value: bytes) -> bytes:
    if not value or any(not _is_digit(byte) for byte in value):
        raise TransformError("numeric slot contains a non-digit")
    output = bytearray()
    offset = 0
    if len(value) & 1:
        output.append(value[0] - 48)
        offset = 1
    while offset < len(value):
        output.append((value[offset] - 48) * 10 + value[offset + 1] - 48)
        offset += 2
    return bytes(output)


def _unpack_digits(data: bytes, length: int) -> bytes:
    expected = (length + 1) // 2
    if len(data) != expected:
        raise TransformError("packed numeric length mismatch")
    output = bytearray()
    offset = 0
    if length & 1:
        if data[0] > 9:
            raise TransformError("invalid leading packed digit")
        output.append(48 + data[0])
        offset = 1
    for value in data[offset:]:
        if value > 99:
            raise TransformError("invalid packed digit pair")
        output.extend((48 + value // 10, 48 + value % 10))
    return bytes(output)


def encode_frame(data: bytes, variant_name: str) -> tuple[bytes, dict[str, int]]:
    variant = VARIANTS[variant_name]
    if variant == 0:
        return data, {
            "raw_bytes": len(data),
            "digit_runs": 0,
            "digit_bytes": 0,
            "slots": 0,
            "main_bytes": len(data),
            "side_bytes": 0,
            "frame_bytes": 0,
            "transformed_bytes": len(data),
            "main_decisions_removed": 0,
        }
    tokens, slots = _tokenize(data, variant)
    main = _serialize_main(tokens, variant)
    ordered = _ordered_slots(tokens, slots, variant)
    if variant <= 2:
        side = b"".join(slot.value for slot in ordered)
    else:
        side = b"".join(_pack_digits(slot.value) for slot in ordered)
    header = (
        MAGIC
        + bytes([variant])
        + _uvarint(len(data))
        + _uvarint(len(main))
        + _uvarint(len(side))
    )
    transformed = header + main + side
    digit_bytes = sum(slot.length for slot in slots)
    digit_runs = len(slots) if variant != 1 else sum(
        1
        for index, byte in enumerate(data)
        if _is_digit(byte) and (index == 0 or not _is_digit(data[index - 1]))
    )
    return transformed, {
        "raw_bytes": len(data),
        "digit_runs": digit_runs,
        "digit_bytes": digit_bytes,
        "slots": len(slots),
        "main_bytes": len(main),
        "side_bytes": len(side),
        "frame_bytes": len(header),
        "transformed_bytes": len(transformed),
        "main_decisions_removed": max(0, digit_bytes - digit_runs),
    }


def decode_frame(frame: bytes) -> bytes:
    if not frame.startswith(MAGIC):
        raise TransformError("missing RADIX-STC frame")
    offset = len(MAGIC)
    if offset >= len(frame):
        raise TransformError("missing variant")
    variant = frame[offset]
    offset += 1
    if variant not in (1, 2, 3, 4):
        raise TransformError("unsupported variant")
    original_length, offset = _read_uvarint(frame, offset)
    main_length, offset = _read_uvarint(frame, offset)
    side_length, offset = _read_uvarint(frame, offset)
    end_main = offset + main_length
    end_side = end_main + side_length
    if end_side != len(frame):
        raise TransformError("frame length mismatch")
    main = frame[offset:end_main]
    side = frame[end_main:end_side]
    tokens, slots = _parse_main(main, variant)
    ordered = _ordered_slots(tokens, slots, variant)
    side_offset = 0
    for slot in ordered:
        width = slot.length if variant <= 2 else (slot.length + 1) // 2
        payload = side[side_offset : side_offset + width]
        if len(payload) != width:
            raise TransformError("truncated side component")
        side_offset += width
        if variant <= 2:
            if any(not _is_digit(value) for value in payload):
                raise TransformError("invalid literal digit payload")
            slot.value = payload
        else:
            slot.value = _unpack_digits(payload, slot.length)
    if side_offset != len(side):
        raise TransformError("unused side-component bytes")
    output = b"".join(
        bytes([token]) if isinstance(token, int) else token.value for token in tokens
    )
    if len(output) != original_length:
        raise TransformError("decoded length mismatch")
    return output


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    encode_parser = subparsers.add_parser("encode")
    encode_parser.add_argument("input")
    encode_parser.add_argument("output")
    encode_parser.add_argument("--variant", choices=VARIANTS, required=True)
    decode_parser = subparsers.add_parser("decode")
    decode_parser.add_argument("input")
    decode_parser.add_argument("output")
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("input")
    args = parser.parse_args()

    input_path = Path(args.input)
    data = input_path.read_bytes()
    if args.command == "encode":
        transformed, stats = encode_frame(data, args.variant)
        Path(args.output).write_bytes(transformed)
        print(json.dumps(stats, sort_keys=True))
    elif args.command == "decode":
        decoded = decode_frame(data)
        Path(args.output).write_bytes(decoded)
        print(json.dumps({"bytes": len(decoded), "sha256": _digest(decoded)}))
    else:
        decoded = decode_frame(data)
        print(
            json.dumps(
                {
                    "frame_bytes": len(data),
                    "decoded_bytes": len(decoded),
                    "decoded_sha256": _digest(decoded),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
