#!/usr/bin/env python3
"""Demultiplex prior-page WikiIR deltas into exact nested column streams.

This discovery probe answers whether the large raw reduction in
``wikiir_prior_page_delta_v1`` is lost only because ADD/COPY/RUN commands and
literal payloads are interleaved.  It reconstructs the byte-identical
interleaved IR and original input, and compares a counted multi-stream bundle
with literal and interleaved LZMA controls.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
from types import ModuleType
from typing import Any


PRESET = 9 | lzma.PRESET_EXTREME
BUNDLE_MAGIC = b"WPC1"
CHANNEL_NAMES = (
    "prefix",
    "suffix",
    "page_modes",
    "literal_lengths",
    "literal_payloads",
    "reference_distances",
    "delta_op_counts",
    "delta_opcodes",
    "add_lengths",
    "add_payloads",
    "copy_positions",
    "copy_lengths",
    "run_values",
    "run_lengths",
)


def _load_delta_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("wikiir_prior_page_delta_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prior-page module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _read_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if position >= len(data) or shift > 63:
            raise ValueError("invalid or truncated varint")
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, position
        shift += 7


def demultiplex(ir: bytes, delta: ModuleType) -> tuple[int, dict[str, bytes]]:
    if not ir.startswith(delta.MAGIC):
        raise ValueError("invalid prior-page IR magic")
    channels = {name: bytearray() for name in CHANNEL_NAMES}
    position = len(delta.MAGIC)
    prefix_length, position = _read_varint(ir, position)
    prefix_end = position + prefix_length
    channels["prefix"].extend(ir[position:prefix_end])
    position = prefix_end
    page_count, position = _read_varint(ir, position)

    for _ in range(page_count):
        mode = ir[position]
        position += 1
        channels["page_modes"].append(mode)
        if mode == delta.MODE_LITERAL:
            length, position = _read_varint(ir, position)
            channels["literal_lengths"].extend(_varint(length))
            end = position + length
            channels["literal_payloads"].extend(ir[position:end])
            position = end
            continue
        if mode != delta.MODE_DELTA:
            raise ValueError("unknown prior-page page mode")
        distance, position = _read_varint(ir, position)
        channels["reference_distances"].extend(_varint(distance))
        delta_length, position = _read_varint(ir, position)
        delta_end = position + delta_length
        op_count = 0
        while position < delta_end:
            opcode = ir[position]
            position += 1
            channels["delta_opcodes"].append(opcode)
            op_count += 1
            if opcode == delta.OP_ADD:
                length, position = _read_varint(ir, position)
                channels["add_lengths"].extend(_varint(length))
                end = position + length
                channels["add_payloads"].extend(ir[position:end])
                position = end
            elif opcode == delta.OP_COPY:
                source, position = _read_varint(ir, position)
                length, position = _read_varint(ir, position)
                channels["copy_positions"].extend(_varint(source))
                channels["copy_lengths"].extend(_varint(length))
            elif opcode == delta.OP_RUN:
                channels["run_values"].append(ir[position])
                position += 1
                length, position = _read_varint(ir, position)
                channels["run_lengths"].extend(_varint(length))
            else:
                raise ValueError("unknown prior-page delta opcode")
        if position != delta_end:
            raise ValueError("delta event exceeds declared length")
        channels["delta_op_counts"].extend(_varint(op_count))

    suffix_length, position = _read_varint(ir, position)
    suffix_end = position + suffix_length
    if suffix_end != len(ir):
        raise ValueError("invalid prior-page suffix")
    channels["suffix"].extend(ir[position:suffix_end])
    return page_count, {name: bytes(value) for name, value in channels.items()}


def multiplex(page_count: int, channels: dict[str, bytes], delta: ModuleType) -> bytes:
    positions = {name: 0 for name in CHANNEL_NAMES}

    def take_varint(name: str) -> int:
        value, positions[name] = _read_varint(channels[name], positions[name])
        return value

    def take(name: str, length: int) -> bytes:
        start = positions[name]
        end = start + length
        if end > len(channels[name]):
            raise ValueError(f"truncated column {name}")
        positions[name] = end
        return channels[name][start:end]

    output = bytearray(delta.MAGIC)
    output.extend(_varint(len(channels["prefix"])))
    output.extend(channels["prefix"])
    positions["prefix"] = len(channels["prefix"])
    output.extend(_varint(page_count))
    for _ in range(page_count):
        mode = take("page_modes", 1)[0]
        output.append(mode)
        if mode == delta.MODE_LITERAL:
            length = take_varint("literal_lengths")
            output.extend(_varint(length))
            output.extend(take("literal_payloads", length))
            continue
        if mode != delta.MODE_DELTA:
            raise ValueError("invalid columnar page mode")
        distance = take_varint("reference_distances")
        op_count = take_varint("delta_op_counts")
        delta_stream = bytearray()
        for _ in range(op_count):
            opcode = take("delta_opcodes", 1)[0]
            delta_stream.append(opcode)
            if opcode == delta.OP_ADD:
                length = take_varint("add_lengths")
                delta_stream.extend(_varint(length))
                delta_stream.extend(take("add_payloads", length))
            elif opcode == delta.OP_COPY:
                source = take_varint("copy_positions")
                length = take_varint("copy_lengths")
                delta_stream.extend(_varint(source))
                delta_stream.extend(_varint(length))
            elif opcode == delta.OP_RUN:
                delta_stream.extend(take("run_values", 1))
                length = take_varint("run_lengths")
                delta_stream.extend(_varint(length))
            else:
                raise ValueError("invalid columnar delta opcode")
        output.extend(_varint(distance))
        output.extend(_varint(len(delta_stream)))
        output.extend(delta_stream)
    output.extend(_varint(len(channels["suffix"])))
    output.extend(channels["suffix"])
    positions["suffix"] = len(channels["suffix"])
    for name in CHANNEL_NAMES:
        if positions[name] != len(channels[name]):
            raise ValueError(f"unconsumed bytes in column {name}")
    return bytes(output)


def _pack_channel(channel: bytes) -> tuple[bytes, dict[str, int | str]]:
    compressed = lzma.compress(channel, preset=PRESET) if channel else b""
    use_compressed = bool(channel) and len(compressed) < len(channel)
    payload = compressed if use_compressed else channel
    packed = (
        bytes([1 if use_compressed else 0])
        + _varint(len(channel))
        + _varint(len(payload))
        + payload
    )
    return packed, {
        "raw_bytes": len(channel),
        "payload_bytes": len(payload),
        "framed_bytes": len(packed),
        "mode": "lzma" if use_compressed else "raw",
    }


def pack_bundle(page_count: int, channels: dict[str, bytes]) -> tuple[bytes, dict[str, Any]]:
    output = bytearray(BUNDLE_MAGIC)
    output.extend(_varint(page_count))
    channel_stats: dict[str, Any] = {}
    for name in CHANNEL_NAMES:
        packed, stats = _pack_channel(channels[name])
        output.extend(packed)
        channel_stats[name] = stats
    return bytes(output), channel_stats


def unpack_bundle(bundle: bytes) -> tuple[int, dict[str, bytes]]:
    if not bundle.startswith(BUNDLE_MAGIC):
        raise ValueError("invalid WikiIR column bundle magic")
    position = len(BUNDLE_MAGIC)
    page_count, position = _read_varint(bundle, position)
    channels: dict[str, bytes] = {}
    for name in CHANNEL_NAMES:
        if position >= len(bundle):
            raise ValueError("truncated WikiIR channel header")
        mode = bundle[position]
        position += 1
        raw_length, position = _read_varint(bundle, position)
        payload_length, position = _read_varint(bundle, position)
        end = position + payload_length
        if end > len(bundle):
            raise ValueError("truncated WikiIR channel payload")
        payload = bundle[position:end]
        position = end
        if mode == 0:
            channel = payload
        elif mode == 1:
            channel = lzma.decompress(payload)
        else:
            raise ValueError("invalid WikiIR channel mode")
        if len(channel) != raw_length:
            raise ValueError("WikiIR channel length mismatch")
        channels[name] = channel
    if position != len(bundle):
        raise ValueError("trailing WikiIR column bundle bytes")
    return page_count, channels


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(input_path: Path, scope_bytes: int, delta_program: Path) -> tuple[dict[str, Any], bytes]:
    delta = _load_delta_module(delta_program)
    raw = input_path.read_bytes()[:scope_bytes]
    ir, delta_stats = delta.encode_ir(raw)
    page_count, channels = demultiplex(ir, delta)
    reconstructed_ir = multiplex(page_count, channels, delta)
    bundle, channel_stats = pack_bundle(page_count, channels)
    unpacked_count, unpacked_channels = unpack_bundle(bundle)
    unpacked_ir = multiplex(unpacked_count, unpacked_channels, delta)
    reconstructed_raw = delta.decode_ir(unpacked_ir)
    literal_archive = lzma.compress(raw, preset=PRESET)
    interleaved_archive = lzma.compress(ir, preset=PRESET)
    source_bytes = Path(__file__).stat().st_size + delta_program.stat().st_size
    exact_ok = bool(
        reconstructed_ir == ir
        and unpacked_ir == ir
        and reconstructed_raw == raw
    )
    receipt = {
        "schema": "wikiir_prior_page_columnar_probe_v1",
        "evidence_level": "discovery_exact_reversible_representation_probe",
        "scope_bytes": len(raw),
        "input": {
            "path": str(input_path.resolve()),
            "sha256": _sha256_bytes(raw),
        },
        "dependency": {
            "path": str(delta_program.resolve()),
            "sha256": _sha256_bytes(delta_program.read_bytes()),
        },
        "delta_stats": delta_stats,
        "channels": channel_stats,
        "metrics": {
            "literal_lzma_bytes": len(literal_archive),
            "interleaved_delta_lzma_bytes": len(interleaved_archive),
            "columnar_bundle_bytes": len(bundle),
            "columnar_gain_vs_literal_lzma_bytes": len(literal_archive) - len(bundle),
            "columnar_gain_vs_interleaved_lzma_bytes": (
                len(interleaved_archive) - len(bundle)
            ),
            "discovery_source_bytes": source_bytes,
            "counted_discovery_score_delta_vs_literal": (
                len(bundle) + source_bytes - len(literal_archive)
            ),
        },
        "identity": {
            "multiplex_equals_original_ir": reconstructed_ir == ir,
            "bundle_roundtrip_equals_original_ir": unpacked_ir == ir,
            "raw_roundtrip_ok": reconstructed_raw == raw,
            "bundle_sha256": _sha256_bytes(bundle),
            "replay_ir_sha256": _sha256_bytes(unpacked_ir),
        },
        "verdict": (
            "columnar_representation_has_backend_headroom"
            if exact_ok and len(bundle) < len(literal_archive)
            else "columnar_shape_does_not_beat_literal_backend"
        ),
        "promotion_authorized": False,
        "claim_boundary": (
            "Discovery-only reversible representation evidence. Source is Python, "
            "the backend is LZMA rather than FX2, and no official score follows."
        ),
    }
    return receipt, bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--delta-program", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    receipt, bundle = run(args.input, args.scope_bytes, args.delta_program)
    args.bundle.parent.mkdir(parents=True, exist_ok=True)
    args.bundle.write_bytes(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
