#!/usr/bin/env python3
"""Prospective independent synthetic TFWC2/transcoder fixtures; no model input.

Reference: astOwOlfo/fx2-cmix-transformer-v1 commit
83f2603f3f7751da5f429fd32669807eb8510494, pysrc/weights_compress.py and
cpp_infer/src/weights_io_compressed.cpp. Upstream repository notice: GNU GPL
version 3; preserve its LICENSE when distributing this derived implementation.

This separate integer-only encoder uses sparse probability keys, while the
C++ transcoder uses dense arrays. It imports neither upstream code nor array,
training, or model libraries. Existence of this source grants no launch authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import prod
from pathlib import Path
import struct

PARENT_MAGIC = b"FX2TFWC2"
TREATMENT_MAGIC = b"GFWPACK1"
DT_I8, DT_BF16, DT_F32, DT_I32 = range(4)
RAW, INT4, BF16, PLANE4, ROPE_SIN, ROPE_COS = range(6)


class ReferenceRangeEncoder:
    """Integer binary coder specified by upstream BinEncoder, with sparse models."""

    def __init__(self):
        self.interval = 0xFFFFFFFF
        self.lower = 0
        self.pending_byte = 0
        self.pending_count = 1
        self.output = bytearray()
        self.probabilities = {}

    def _flush_resolved_bytes(self):
        if self.lower < 0xFF000000 or self.lower >> 32:
            carry = self.lower >> 32
            self.output.append((self.pending_byte + carry) & 255)
            self.output.extend(bytes([(255 + carry) & 255]) * (self.pending_count - 1))
            self.pending_byte = (self.lower >> 24) & 255
            self.pending_count = 0
        self.pending_count += 1
        self.lower = (self.lower & 0xFFFFFF) << 8

    def symbol(self, family, context, width, value):
        if not 0 <= value < 1 << width:
            raise ValueError("symbol outside encoded tree")
        prefix = 1
        for shift in range(width - 1, -1, -1):
            key = (family, context, prefix)
            probability = self.probabilities.get(key, 1024)
            boundary = (self.interval >> 11) * probability
            bit = (value >> shift) & 1
            if bit:
                self.lower += boundary
                self.interval -= boundary
                probability -= probability >> 5
            else:
                self.interval = boundary
                probability += (2048 - probability) >> 5
            self.probabilities[key] = probability
            while self.interval < 1 << 24:
                self.interval <<= 8
                self._flush_resolved_bytes()
            prefix = prefix * 2 + bit

    def finish(self):
        for _ in range(5):
            self._flush_resolved_bytes()
        return bytes(self.output)


def tensor(name, dtype, shape, encoding, payload=()):
    """Payload is signed INT4 values or exact byte patterns; RoPE has no payload."""
    return {"name": name, "dtype": dtype, "shape": tuple(shape), "encoding": encoding,
            "payload": tuple(payload) if encoding == INT4 else bytes(payload)}


def encode_reference(tensors, *, treatment=False, reset_rows=True, reset_tensors=True,
                     invalid_metadata=False):
    """Write the format grammar directly, without deserializing any real weights.

    Zero-dimensional tensors are accepted by both pinned readers (one element).
    Their direct grammar fixture does not claim that NumPy's contiguous-array
    conversion in the upstream exporter preserves zero dimensions.
    """
    encoder = ReferenceRangeEncoder()
    previous_meta = 0

    def meta(value):
        nonlocal previous_meta
        encoder.symbol("metadata", previous_meta, 8, value)
        previous_meta = value

    for index, entry in enumerate(tensors):
        name = entry["name"].encode("utf-8")
        shape, dtype, encoding = entry["shape"], entry["dtype"], entry["encoding"]
        if len(name) > 255 or len(shape) > 255:
            raise ValueError("unrepresentable metadata")
        meta(len(name))
        previous_two = (0, 0)
        for byte in name:
            encoder.symbol("name", previous_two, 8, byte)
            previous_two = (previous_two[1], byte)
        meta(dtype)
        meta(len(shape))
        for extent in shape:
            for byte in struct.pack("<I", extent):
                meta(byte)
        meta(encoding)
        count = prod(shape)
        width = 1 if dtype == DT_I8 else 2 if dtype == DT_BF16 else 4
        payload = entry["payload"]
        if not invalid_metadata:
            if encoding == INT4 and (dtype != DT_I8 or len(payload) != count or any(not -7 <= x <= 7 for x in payload)):
                raise ValueError("invalid INT4 fixture")
            if encoding == BF16 and dtype != DT_BF16:
                raise ValueError("invalid BF16 fixture")
            if encoding == PLANE4 and dtype not in (DT_F32, DT_I32):
                raise ValueError("invalid four-byte fixture")
            if encoding not in (INT4, ROPE_SIN, ROPE_COS) and len(payload) != count * width:
                raise ValueError("payload length does not match tensor")
        if encoding == INT4:
            previous_symbol = 15
            row_width = shape[-1] if shape else 1
            for offset, signed in enumerate(payload):
                if reset_rows and row_width and offset % row_width == 0:
                    previous_symbol = 15
                context = ((index if reset_tensors else 0), previous_symbol) if treatment else 0
                symbol = signed + 7
                encoder.symbol("int4", context, 4, symbol)
                previous_symbol = symbol
        elif encoding == BF16:
            if len(payload) % 2:
                raise ValueError("BF16 fixture requires complete words")
            for offset in range(0, len(payload), 2):
                low, high = payload[offset:offset + 2]
                encoder.symbol("bf16_high", 0, 8, high)
                encoder.symbol("bf16_low", high, 8, low)
        elif encoding == PLANE4:
            for offset, byte in enumerate(payload):
                encoder.symbol("plane", offset % 4, 8, byte)
        elif encoding == RAW:
            for byte in payload:
                encoder.symbol("raw", 0, 8, byte)
        elif encoding not in (ROPE_SIN, ROPE_COS) and not invalid_metadata:
            raise ValueError("unknown encoding")
    magic = TREATMENT_MAGIC if treatment else PARENT_MAGIC
    return magic + struct.pack("<I", len(tensors)) + encoder.finish()


def valid_populations():
    signed = tuple(range(-7, 8))
    rows = (7, 7, 7, 7, -7, -7, -7, -7, 0, 0, 0, 0, 7, -7, 7, -7)
    all_tags = [
        tensor("quant.scalar", DT_I8, (), INT4, (-7,)),
        tensor("quant.signed", DT_I8, (3, 5), INT4, signed),
        tensor("quant.rows", DT_I8, (4, 4), INT4, rows),
        tensor("quant.rows.second", DT_I8, (4, 4), INT4, tuple(reversed(rows))),
        tensor("bf16.bits", DT_BF16, (2, 3), BF16,
               struct.pack("<6H", 0, 0x8000, 0x3F80, 0x7F80, 0xFF80, 0x7FC1)),
        tensor("f32.bits", DT_F32, (2, 3), PLANE4,
               struct.pack("<6I", 0, 0x80000000, 0x3F800000, 0x7F800000, 0xFF800000, 0x7FC00001)),
        tensor("i32.bits", DT_I32, (4,), PLANE4, struct.pack("<4i", -(1 << 31), -1, 0, (1 << 31) - 1)),
        tensor("raw.i8", DT_I8, (6,), RAW, struct.pack("<6b", -128, -8, -1, 0, 8, 127)),
        tensor("rope.inv_freq", DT_F32, (2,), PLANE4, struct.pack("<2f", 1.0, 0.5)),
        # Position zero: upstream CUDA-compatible reconstruction is exactly
        # sin(0)=+0 and cos(0)=1 for both columns, with no stored table payload.
        tensor("rope.sin", DT_F32, (1, 2), ROPE_SIN),
        tensor("rope.cos", DT_F32, (1, 2), ROPE_COS),
        tensor("empty.int4", DT_I8, (0, 3), INT4),
        tensor("empty.last.dimension", DT_I8, (2, 0), INT4),
        tensor("empty.bf16", DT_BF16, (0,), BF16),
        tensor("empty.f32", DT_F32, (0,), PLANE4),
        tensor("empty.i32", DT_I32, (0,), PLANE4),
    ]
    return {"zero_tensors": [], "all_tags_and_rows": all_tags,
            "row_width_one": [tensor("single.columns", DT_I8, (15, 1), INT4, signed)],
            "scalar_f32": [tensor("scalar.f32", DT_F32, (), PLANE4, struct.pack("<I", 0x80000000))],
            "range_adaptation_stress": [tensor("range.stress", DT_I8, (64, 64), INT4,
                                                tuple((index * 13 + index // 7) % 15 - 7 for index in range(4096)))],
            "maximum_native_dimensions": [tensor("eight.dimensions", DT_I8, (1,) * 8, INT4, (7,))]}


def malformed_populations():
    q = tensor("duplicate", DT_I8, (1,), INT4, (0,))
    return {
        "duplicate_names": [q, q],
        "unknown_dtype": [tensor("bad", 4, (), 255)],
        "too_many_dimensions": [tensor("bad", DT_I8, (1,) * 9, INT4, (0,))],
        "unknown_encoding": [tensor("bad", DT_I8, (1,), 255)],
        "int4_wrong_dtype": [tensor("bad", DT_F32, (1,), INT4, (0,))],
        "bf16_wrong_dtype": [tensor("bad", DT_I8, (1,), BF16, b"\0\0")],
        "plane_wrong_dtype": [tensor("bad", DT_I8, (1,), PLANE4, b"\0")],
        # The generic reader can represent symbol 15, but the pinned writer's
        # INT4 branch emits only 0..14; +8 must use RAW. The probe rejects it.
        "int4_outside_public_writer_domain": [tensor("bad", DT_I8, (1,), INT4, (8,))],
        "rope_missing_inverse_frequency": [tensor("rope.sin", DT_F32, (1, 2), ROPE_SIN)],
        "rope_wrong_dtype": [tensor("rope.sin", DT_BF16, (1, 2), ROPE_SIN)],
        "rope_wrong_frequency_shape": [
            tensor("rope.inv_freq", DT_F32, (3,), PLANE4, struct.pack("<3f", 1.0, 0.5, 0.25)),
            tensor("rope.cos", DT_F32, (1, 2), ROPE_COS)],
        "rope_nonvector_frequency": [
            tensor("rope.inv_freq", DT_F32, (1, 2), PLANE4, struct.pack("<2f", 1.0, 0.5)),
            tensor("rope.cos", DT_F32, (1, 2), ROPE_COS)],
        "extent_exceeds_probe_bound": [tensor("bad", DT_I8, (0xFFFFFFFF, 0xFFFFFFFF), RAW)],
    }


def raw_reference(tensors):
    """FX2TFW01 tensors for the unchanged upstream loader comparison binary."""
    output = bytearray(b"FX2TFW01" + struct.pack("<I", len(tensors)))
    for entry in tensors:
        name, shape = entry["name"].encode(), entry["shape"]
        output.extend(struct.pack("<I", len(name)) + name)
        output.extend(struct.pack("<BI", entry["dtype"], len(shape)))
        output.extend(struct.pack("<" + "I" * len(shape), *shape))
        if entry["encoding"] == INT4:
            output.extend(struct.pack("<" + "b" * len(entry["payload"]), *entry["payload"]))
        elif entry["encoding"] in (ROPE_SIN, ROPE_COS):
            if entry["dtype"] != DT_F32 or shape != (1, 2):
                raise ValueError("raw RoPE golden fixture supports only the declared position-zero case")
            output.extend(struct.pack("<I", 0 if entry["encoding"] == ROPE_SIN else 0x3F800000) * prod(shape))
        else:
            output.extend(entry["payload"])
    return bytes(output)


def _reference(path, data):
    with path.open("xb") as handle:
        handle.write(data)
    return {"path": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare(destination: Path):
    """Create a new synthetic fixture directory only when explicitly executed."""
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema": "gamma.fx2-weight-pack-synthetic-fixtures.v1",
        "upstream_commit": "83f2603f3f7751da5f429fd32669807eb8510494",
        "real_model_accessed": False, "objective_credit_bytes": 0,
        "valid": [], "rejection": [], "comparison_controls": [],
        "integrity_boundary": "TFWC2 has no authenticated checksum. Arbitrary corruption may encode a different valid model; pin the input hash before invocation.",
        "scalar_boundary": "Zero dimensions are accepted by both pinned readers. Direct grammar fixtures do not assert upstream NumPy exporter behavior.",
        "strict_subset_rejections": ["int4_outside_public_writer_domain", "extent_exceeds_probe_bound", "rope_nonvector_frequency"],
    }
    populations = valid_populations()
    for name, tensors in populations.items():
        parent = encode_reference(tensors)
        treatment = encode_reference(tensors, treatment=True)
        if name == "zero_tensors" and parent != PARENT_MAGIC + b"\0" * 9:
            raise AssertionError("independent zero-tensor golden bytes disagree")
        represented = sum(prod(t["shape"]) * (1 if t["dtype"] == DT_I8 else 2 if t["dtype"] == DT_BF16 else 4) for t in tensors)
        regenerated = sum(prod(t["shape"]) * 4 for t in tensors if t["encoding"] in (ROPE_SIN, ROPE_COS))
        manifest["valid"].append({
            "id": name, "parent": _reference(destination / (name + ".tfwc2"), parent),
            "expected_treatment": _reference(destination / (name + ".gfwpack1"), treatment),
            "raw_reference": _reference(destination / (name + ".weights.bin"), raw_reference(tensors)),
            "tensor_count": len(tensors), "tensor_payload_bytes": represented - regenerated,
            "regenerated_rope_bytes": regenerated,
            "required": "parent regeneration equals parent; pack equals independent treatment; unpack equals parent; repeat pack identity",
        })
    base = encode_reference(populations["all_tags_and_rows"])
    negative_bytes = {
        "bad_magic": b"BADMAGIC" + base[8:],
        "nonzero_initial_cache": base[:12] + b"\1" + base[13:],
        "truncated_header": base[:11],
        "truncated_stream": base[:len(base) // 2],
        "missing_final_flush_byte": base[:-1],
        "extra_trailing_byte": base + b"\0",
        "tensor_count_exceeds_probe_bound": base[:8] + struct.pack("<I", 4097) + base[12:],
    }
    negative_bytes.update({name: encode_reference(tensors, invalid_metadata=True)
                           for name, tensors in malformed_populations().items()})
    for name, data in negative_bytes.items():
        manifest["rejection"].append({"id": name, "input": _reference(destination / (name + ".tfwc2"), data),
                                      "required": "nonzero exit with no published output"})
    for name, options in (("missing_row_reset", {"reset_rows": False}),
                          ("missing_tensor_reset", {"reset_tensors": False})):
        data = encode_reference(populations["all_tags_and_rows"], treatment=True, **options)
        if data == encode_reference(populations["all_tags_and_rows"], treatment=True):
            raise AssertionError("context control did not distinguish " + name)
        manifest["comparison_controls"].append({
            "id": name, "input": _reference(destination / (name + ".gfwpack1"), data),
            "required": "must differ from independent correct treatment; reject or fail exact-parent restoration",
        })
    corrupt = bytearray(base)
    corrupt[len(corrupt) // 2] ^= 0x20
    manifest["comparison_controls"].append({
        "id": "bit_corruption", "input": _reference(destination / "bit_corruption.tfwc2", bytes(corrupt)),
        "required": "input hash must differ from pinned parent and be rejected by admission; decoder rejection alone is not guaranteed",
        "expected_parent_sha256": hashlib.sha256(base).hexdigest(),
    })
    source = Path(__file__).read_bytes()
    manifest["generator_sha256"] = hashlib.sha256(source).hexdigest()
    with (destination / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output_dir)


if __name__ == "__main__":
    main()
