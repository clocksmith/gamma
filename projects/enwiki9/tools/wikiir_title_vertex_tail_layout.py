#!/usr/bin/env python3
"""Repack title-as-vertex WikiIR with the text skeleton before its directory."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import struct
from types import ModuleType
from typing import Any


BASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "programs/wikiir_title_vertex_v1/program.py"
)
TAIL_MAGIC = b"WVT2"
TRAILER_BYTES = 12


def _load_base() -> ModuleType:
    spec = importlib.util.spec_from_file_location("wikiir_title_vertex_tail_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load title-vertex base: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load_base()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_front(stream: bytes) -> tuple[bytes, bytes, dict[str, int]]:
    if not stream.startswith(BASE.MAGIC):
        raise ValueError("invalid front title-vertex magic")
    position = len(BASE.MAGIC)
    title_count, position = BASE._read_varint(stream, position)
    dictionary_length, position = BASE._read_varint(stream, position)
    dictionary_end = position + dictionary_length
    if dictionary_end > len(stream):
        raise ValueError("truncated front title dictionary")
    dictionary = stream[position:dictionary_end]
    position = dictionary_end
    skeleton_length, position = BASE._read_varint(stream, position)
    skeleton_end = position + skeleton_length
    if skeleton_end > len(stream):
        raise ValueError("truncated front title skeleton")
    skeleton = stream[position:skeleton_end]
    position = skeleton_end
    link_count, position = BASE._read_varint(stream, position)
    if position >= len(stream):
        raise ValueError("missing front title ID mode")
    id_mode = stream[position]
    position += 1
    id_length, position = BASE._read_varint(stream, position)
    id_end = position + id_length
    if id_end != len(stream):
        raise ValueError("invalid front title ID stream")
    id_payload = stream[position:id_end]

    metadata = bytearray()
    metadata.extend(BASE._varint(title_count))
    metadata.extend(BASE._varint(dictionary_length))
    metadata.extend(dictionary)
    metadata.extend(BASE._varint(link_count))
    metadata.append(id_mode)
    metadata.extend(BASE._varint(id_length))
    metadata.extend(id_payload)
    return skeleton, bytes(metadata), {
        "title_count": title_count,
        "dictionary_bytes": dictionary_length,
        "skeleton_bytes": skeleton_length,
        "link_count": link_count,
        "id_stream_bytes": id_length,
    }


def _pack_tail(front: bytes) -> tuple[bytes, dict[str, int]]:
    skeleton, metadata, stats = _split_front(front)
    output = skeleton + metadata + struct.pack("<Q", len(metadata)) + TAIL_MAGIC
    return output, {
        **stats,
        "metadata_bytes": len(metadata),
        "trailer_bytes": TRAILER_BYTES,
        "tail_ir_bytes": len(output),
        "tail_layout_delta_vs_front_bytes": len(output) - len(front),
    }


def decode_ir(stream: bytes) -> bytes:
    if len(stream) < TRAILER_BYTES or stream[-4:] != TAIL_MAGIC:
        raise ValueError("invalid tail title-vertex trailer")
    metadata_length = struct.unpack_from("<Q", stream, len(stream) - TRAILER_BYTES)[0]
    if metadata_length > len(stream) - TRAILER_BYTES:
        raise ValueError("invalid tail title-vertex metadata length")
    metadata_start = len(stream) - TRAILER_BYTES - metadata_length
    skeleton = stream[:metadata_start]
    metadata = stream[metadata_start : len(stream) - TRAILER_BYTES]
    position = 0
    title_count, position = BASE._read_varint(metadata, position)
    dictionary_length, position = BASE._read_varint(metadata, position)
    dictionary_end = position + dictionary_length
    if dictionary_end > len(metadata):
        raise ValueError("truncated tail title dictionary")
    titles, decoded_end = BASE._decode_dictionary(metadata, position, title_count)
    if decoded_end != dictionary_end:
        raise ValueError("tail title dictionary length mismatch")
    position = dictionary_end
    link_count, position = BASE._read_varint(metadata, position)
    if position >= len(metadata):
        raise ValueError("missing tail title ID mode")
    id_mode = metadata[position]
    position += 1
    id_length, position = BASE._read_varint(metadata, position)
    id_end = position + id_length
    if id_end != len(metadata):
        raise ValueError("invalid tail title ID stream length")
    link_ids = BASE._decode_ids(id_mode, metadata[position:id_end], link_count)
    return BASE._restore_skeleton(skeleton, titles, link_ids)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    front, base_stats = BASE.encode_ir(data)
    tail, layout_stats = _pack_tail(front)
    return tail, {**base_stats, **layout_stats, "layout": "text_skeleton_then_directory"}


def run(input_path: Path, scope_bytes: int) -> tuple[bytes, dict[str, Any]]:
    with input_path.open("rb") as stream:
        raw = stream.read(scope_bytes)
    if len(raw) != scope_bytes:
        raise ValueError("input is shorter than the declared scope")
    first, stats = encode_ir(raw)
    second, second_stats = encode_ir(raw)
    roundtrip_ok = decode_ir(first) == raw
    determinism_ok = first == second and stats == second_stats
    if not roundtrip_ok or not determinism_ok:
        raise RuntimeError("tail title-vertex identity failure")
    literal_archive = lzma.compress(raw, preset=BASE.PRESET)
    tail_archive = lzma.compress(first, preset=BASE.PRESET)
    receipt = {
        "schema": "wikiir_title_vertex_tail_layout_v1",
        "evidence_level": "exact_reversible_representation_prefix",
        "scope_bytes": scope_bytes,
        "input": {
            "path": str(input_path.resolve()),
            "scoped_sha256": sha256_bytes(raw),
        },
        "implementation": {
            "tool": str(Path(__file__).resolve()),
            "tool_bytes": Path(__file__).stat().st_size,
            "tool_sha256": sha256(Path(__file__)),
            "base_program": str(BASE_PATH.resolve()),
            "base_program_bytes": BASE_PATH.stat().st_size,
            "base_program_sha256": sha256(BASE_PATH),
            "counted_discovery_source_bytes": Path(__file__).stat().st_size + BASE_PATH.stat().st_size,
        },
        "ir": {"bytes": len(first), "sha256": sha256_bytes(first)},
        "stats": stats,
        "proxy": {
            "literal_lzma_archive_bytes": len(literal_archive),
            "tail_lzma_archive_bytes": len(tail_archive),
            "tail_lzma_delta_bytes": len(tail_archive) - len(literal_archive),
        },
        "identity": {
            "raw_ir_roundtrip_ok": roundtrip_ok,
            "encode_ir_deterministic": determinism_ok,
            "selected_information_identical_to_front_layout": True,
        },
        "promotion_authorized": False,
        "claim_boundary": "Layout-isolation discovery only; target-backend and counted native proof remain.",
    }
    return first, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--output-ir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    ir, receipt = run(args.input, args.scope_bytes)
    args.output_ir.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary_ir = args.output_ir.with_suffix(args.output_ir.suffix + ".tmp")
    temporary_receipt = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
    temporary_ir.write_bytes(ir)
    receipt["ir"]["path"] = str(args.output_ir.resolve())
    temporary_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary_ir, args.output_ir)
    os.replace(temporary_receipt, args.receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
