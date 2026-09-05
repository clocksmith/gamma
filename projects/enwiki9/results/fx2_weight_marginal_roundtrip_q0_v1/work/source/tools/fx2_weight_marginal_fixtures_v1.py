#!/usr/bin/env python3
"""Independent synthetic FX2 fixed-marginal fixtures; no real model input.

Parent format/range arithmetic: astOwOlfo/fx2-cmix-transformer-v1 commit
83f2603f3f7751da5f429fd32669807eb8510494, pysrc/weights_compress.py and
cpp_infer/src/weights_io_compressed.cpp. Upstream notice: GNU GPL version 3;
preserve its LICENSE when distributing this derived implementation.

GFX2MAR1 stores tensor_count:u32, mode:u8 (D=1,G=2), INT4_count:u32,
15 global u32 counts, then sorted (tensor_index:u32,15 local u32 counts).
The unchanged metadata/non-INT4 range stream follows at 77+64*INT4_count.
INT4 probabilities are fixed, derived from the chosen 15-bin histogram;
the sixteenth leaf has count zero. D/G carry identical side information.
This stdlib-only writer does not import the C++ implementation or sealed q0
fixture source. Creating this source grants no execution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import prod
from pathlib import Path
import struct

PARENT_MAGIC, MARGINAL_MAGIC = b"FX2TFWC2", b"GFX2MAR1"
DT_I8, DT_BF16, DT_F32, DT_I32 = range(4)
RAW, INT4, BF16, PLANE4, ROPE_SIN, ROPE_COS = range(6)


class RangeWriter:
    """Sparse independent integer encoder matching the public binary coder."""

    def __init__(self):
        self.interval, self.lower = 0xFFFFFFFF, 0
        self.pending_byte, self.pending_count = 0, 1
        self.output, self.probabilities = bytearray(), {}

    def shift_low(self):
        if self.lower < 0xFF000000 or self.lower >> 32:
            carry = self.lower >> 32
            self.output.append((self.pending_byte + carry) & 255)
            self.output.extend(bytes([(255 + carry) & 255]) * (self.pending_count - 1))
            self.pending_byte = (self.lower >> 24) & 255
            self.pending_count = 0
        self.pending_count += 1
        self.lower = (self.lower & 0xFFFFFF) << 8

    def bit(self, probability, bit):
        boundary = (self.interval >> 11) * probability
        if bit:
            self.lower += boundary
            self.interval -= boundary
            updated = probability - (probability >> 5)
        else:
            self.interval = boundary
            updated = probability + ((2048 - probability) >> 5)
        while self.interval < 1 << 24:
            self.interval <<= 8
            self.shift_low()
        return updated

    def symbol(self, family, context, width, value, fixed=None):
        if not 0 <= value < 1 << width:
            raise ValueError("symbol outside encoded tree")
        node = 1
        for shift in range(width - 1, -1, -1):
            bit = (value >> shift) & 1
            if fixed is None:
                key = (family, context, node)
                self.probabilities[key] = self.bit(self.probabilities.get(key, 1024), bit)
            else:
                self.bit(fixed[node], bit)
            node = node * 2 + bit

    def finish(self):
        for _ in range(5):
            self.shift_low()
        return bytes(self.output)


def fixed_tree(counts):
    """16-leaf tree, nearest-integer p0 (half up), clamped to 1..2047."""
    if len(counts) != 15 or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError("invalid histogram")
    leaves = list(counts) + [0]
    probabilities = [1024] * 16
    for node in range(1, 16):
        depth = node.bit_length() - 1
        width = 1 << (4 - depth)
        start = (node - (1 << depth)) * width
        left = sum(leaves[start:start + width // 2])
        total = sum(leaves[start:start + width])
        if total:
            probabilities[node] = max(1, min(2047, (2048 * left + total // 2) // total))
    return probabilities


def tensor(name, dtype, shape, encoding, payload=()):
    return {"name": name, "dtype": dtype, "shape": tuple(shape), "encoding": encoding,
            "payload": tuple(payload) if encoding == INT4 else bytes(payload)}


def histograms(tensors):
    result = {}
    for index, entry in enumerate(tensors):
        if entry["encoding"] == INT4:
            counts = [0] * 15
            for value in entry["payload"]:
                if not -7 <= value <= 7:
                    raise ValueError("INT4 value outside public writer domain")
                counts[value + 7] += 1
            result[index] = counts
    return result


def header(tensor_count, mode, local):
    global_counts = [sum(counts[k] for counts in local.values()) for k in range(15)]
    output = bytearray(MARGINAL_MAGIC + struct.pack("<IBI", tensor_count, {"D": 1, "G": 2}[mode], len(local)))
    output.extend(struct.pack("<15I", *global_counts))
    for index, counts in sorted(local.items()):
        output.extend(struct.pack("<16I", index, *counts))
    return bytes(output), global_counts


def encode_reference(tensors, mode="P", *, invalid_metadata=False, supplied_histograms=None):
    """Write events directly; supplied histograms intentionally permit false counts.

    False histograms are used for both the header and coding probabilities, so
    decoding preserves the fixture symbols and must reject the count mismatch.
    """
    if mode not in ("P", "K", "D", "G"):
        raise ValueError("unknown reference mode")
    writer = RangeWriter()
    prefix = PARENT_MAGIC + struct.pack("<I", len(tensors))
    trees, global_tree = {}, None
    if mode in ("D", "G"):
        local = histograms(tensors) if supplied_histograms is None else supplied_histograms
        prefix, global_counts = header(len(tensors), mode, local)
        trees = {index: fixed_tree(counts) for index, counts in local.items()}
        global_tree = fixed_tree(global_counts)
    previous_meta = 0

    def meta(value):
        nonlocal previous_meta
        writer.symbol("metadata", previous_meta, 8, value)
        previous_meta = value

    for index, entry in enumerate(tensors):
        name = entry["name"].encode("utf-8")
        dtype, shape, encoding = entry["dtype"], entry["shape"], entry["encoding"]
        if len(name) > 255 or len(shape) > 255:
            raise ValueError("unrepresentable metadata")
        meta(len(name))
        previous_two = (0, 0)
        for value in name:
            writer.symbol("name", previous_two, 8, value)
            previous_two = (previous_two[1], value)
        meta(dtype)
        meta(len(shape))
        for extent in shape:
            for value in struct.pack("<I", extent):
                meta(value)
        meta(encoding)
        count = prod(shape)
        width = 1 if dtype == DT_I8 else 2 if dtype == DT_BF16 else 4
        payload = entry["payload"]
        if not invalid_metadata:
            if dtype not in range(4) or encoding not in range(6):
                raise ValueError("invalid type/encoding")
            if encoding == INT4 and (dtype != DT_I8 or len(payload) != count or any(not -7 <= q <= 7 for q in payload)):
                raise ValueError("invalid INT4 fixture")
            if encoding == BF16 and dtype != DT_BF16:
                raise ValueError("invalid BF16 fixture")
            if encoding == PLANE4 and width != 4:
                raise ValueError("invalid plane fixture")
            if encoding not in (INT4, ROPE_SIN, ROPE_COS) and len(payload) != count * width:
                raise ValueError("payload length differs from shape")
        if encoding == INT4:
            selected = trees[index] if mode == "D" else global_tree
            for value in payload:
                writer.symbol("int4", 0, 4, value + 7, selected)
        elif encoding == BF16:
            if len(payload) % 2:
                raise ValueError("partial BF16 word")
            for offset in range(0, len(payload), 2):
                low, high = payload[offset:offset + 2]
                writer.symbol("bf16_hi", 0, 8, high)
                writer.symbol("bf16_lo", high, 8, low)
        elif encoding == PLANE4:
            for offset, value in enumerate(payload):
                writer.symbol("plane", offset % 4, 8, value)
        elif encoding == RAW:
            for value in payload:
                writer.symbol("raw", 0, 8, value)
    return prefix + writer.finish()


def valid_populations():
    signed = tuple(range(-7, 8))
    return {
        "zero_tensors": [],
        "uniform_marginal": [tensor("uniform", DT_I8, (16, 15), INT4, signed * 16)],
        "skewed_marginal": [tensor("skewed", DT_I8, (16, 16), INT4,
                                    tuple(-7 if k % 32 == 0 else 7 if k % 32 == 1 else 0 for k in range(256)))],
        "heterogeneous_tensors": [
            tensor("negative", DT_I8, (8, 8), INT4, (-7,) * 63 + (0,)),
            tensor("positive", DT_I8, (8, 8), INT4, (7,) * 63 + (0,)),
            tensor("empty.middle", DT_I8, (0, 8), INT4)],
        "empty_and_scalar": [
            tensor("scalar.int4", DT_I8, (), INT4, (-7,)),
            tensor("scalar.f32", DT_F32, (), PLANE4, struct.pack("<I", 0x80000000)),
            tensor("empty.first", DT_I8, (0, 3), INT4),
            tensor("empty.last", DT_I8, (2, 0), INT4)],
        "all_tags_and_rows": [
            tensor("quant.signed", DT_I8, (3, 5), INT4, signed),
            tensor("bf16.bits", DT_BF16, (2, 3), BF16, struct.pack("<6H", 0, 0x8000, 0x3F80, 0x7F80, 0xFF80, 0x7FC1)),
            tensor("f32.bits", DT_F32, (2, 3), PLANE4, struct.pack("<6I", 0, 0x80000000, 0x3F800000, 0x7F800000, 0xFF800000, 0x7FC00001)),
            tensor("i32.bits", DT_I32, (4,), PLANE4, struct.pack("<4i", -(1 << 31), -1, 0, (1 << 31) - 1)),
            tensor("raw.i8", DT_I8, (6,), RAW, struct.pack("<6b", -128, -8, -1, 0, 8, 127)),
            tensor("rope.inv_freq", DT_F32, (2,), PLANE4, struct.pack("<2f", 1.0, 0.5)),
            tensor("rope.sin", DT_F32, (1, 2), ROPE_SIN),
            tensor("rope.cos", DT_F32, (1, 2), ROPE_COS),
            tensor("empty.bf16", DT_BF16, (0,), BF16),
            tensor("empty.f32", DT_F32, (0,), PLANE4),
            tensor("empty.i32", DT_I32, (0,), PLANE4)],
        "range_adaptation_stress": [
            tensor("range.stress", DT_I8, (64, 64), INT4,
                   tuple((k * 13 + k // 7) % 15 - 7 for k in range(4096))),
            # At the root, 2048*3/4096 = 1.5: half-up must produce 2,
            # which distinguishes the rounding rule from flooring before clamp.
            tensor("rounding.half.up", DT_I8, (64, 64), INT4, (-7,) * 3 + (7,) * 4093)],
        "maximum_native_dimensions": [tensor("eight.dimensions", DT_I8, (1,) * 8, INT4, (7,))],
    }


def raw_reference(tensors):
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
                raise ValueError("raw RoPE golden supports only the declared position-zero case")
            output.extend(struct.pack("<I", 0 if entry["encoding"] == ROPE_SIN else 0x3F800000) * prod(shape))
        else:
            output.extend(entry["payload"])
    return bytes(output)


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
        "int4_outside_public_writer_domain": [tensor("bad", DT_I8, (1,), INT4, (8,))],
        "rope_missing_frequency": [tensor("rope.sin", DT_F32, (1, 2), ROPE_SIN)],
        "rope_wrong_dtype": [tensor("rope.sin", DT_BF16, (1, 2), ROPE_SIN)],
        "rope_wrong_frequency_shape": [tensor("rope.inv_freq", DT_F32, (3,), PLANE4, struct.pack("<3f", 1.0, 0.5, 0.25)), tensor("rope.cos", DT_F32, (1, 2), ROPE_COS)],
        "rope_nonvector_frequency": [tensor("rope.inv_freq", DT_F32, (1, 2), PLANE4, struct.pack("<2f", 1.0, 0.5)), tensor("rope.cos", DT_F32, (1, 2), ROPE_COS)],
        "extent_exceeds_bound": [tensor("bad", DT_I8, (0xFFFFFFFF, 0xFFFFFFFF), RAW)],
    }


def replace_u32(data, offset, value):
    return data[:offset] + struct.pack("<I", value) + data[offset + 4:]


def rejection_streams(populations):
    parent = encode_reference(populations["all_tags_and_rows"])
    tensors = populations["heterogeneous_tensors"]
    marginal = encode_reference(tensors, "D")
    stream_offset = 77 + 64 * len(histograms(tensors))
    cases = {name: ("P", encode_reference(values, invalid_metadata=True)) for name, values in malformed_populations().items()}
    for name, data in {
        "parent_bad_magic": b"BADMAGIC" + parent[8:],
        "parent_nonzero_cache": parent[:12] + b"\1" + parent[13:],
        "parent_truncated_header": parent[:11],
        "parent_truncated_stream": parent[:len(parent) // 2],
        "parent_missing_flush": parent[:-1],
        "parent_trailing_byte": parent + b"\0",
        "parent_tensor_limit": replace_u32(parent, 8, 4097),
    }.items():
        cases[name] = ("P", data)
    for name, data in {
        "marginal_bad_magic": b"BADMAGIC" + marginal[8:],
        "marginal_bad_mode": marginal[:12] + b"\0" + marginal[13:],
        "marginal_truncated_header": marginal[:76],
        "marginal_truncated_record": marginal[:77 + 63],
        "marginal_truncated_stream": marginal[:stream_offset + 4],
        "marginal_nonzero_cache": marginal[:stream_offset] + b"\1" + marginal[stream_offset + 1:],
        "marginal_missing_flush": marginal[:-1],
        "marginal_trailing_byte": marginal + b"\0",
        "marginal_tensor_limit": replace_u32(marginal, 8, 4097),
        "marginal_record_limit": replace_u32(marginal, 13, 4097),
        "marginal_global_sum_mismatch": replace_u32(marginal, 17, 64),
        "marginal_count_exceeds_bound": replace_u32(marginal, 17, 0xFFFFFFFF),
        "marginal_duplicate_index": replace_u32(marginal, 77 + 64, 0),
        "marginal_index_out_of_range": replace_u32(marginal, 77, len(tensors)),
        "marginal_unsorted_indices": marginal[:77] + marginal[141:205] + marginal[77:141] + marginal[205:],
        "marginal_missing_empty_record": replace_u32(marginal[:205] + marginal[269:], 13, 2),
    }.items():
        cases[name] = ("restore", data)
    mixed = encode_reference(populations["all_tags_and_rows"], "D")
    cases["marginal_record_on_nonint4"] = ("restore", replace_u32(mixed, 77, 1))
    wrong = histograms(tensors)
    wrong[0] = wrong[0].copy()
    wrong[0][0] -= 1
    wrong[0][1] += 1
    for mode in ("D", "G"):
        cases["marginal_actual_counts_differ_" + mode] = ("restore", encode_reference(tensors, mode, supplied_histograms=wrong))
    wrong_total = histograms(tensors)
    wrong_total[0] = wrong_total[0].copy()
    wrong_total[0][0] += 1
    cases["marginal_local_sum_differs_from_shape"] = ("restore", encode_reference(tensors, "D", supplied_histograms=wrong_total))
    return cases


def write_ref(destination, filename, data):
    with (destination / filename).open("xb") as handle:
        handle.write(data)
    return {"path": filename, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare(destination):
    destination.mkdir(parents=True, exist_ok=False)
    populations = valid_populations()
    manifest = {"schema": "gamma.fx2-weight-marginal-synthetic-fixtures.v1",
                "upstream_commit": "83f2603f3f7751da5f429fd32669807eb8510494",
                "real_model_accessed": False, "objective_credit_bytes": 0,
                "valid": [], "rejection": [], "comparison_controls": [], "output_controls": [],
                "integrity_boundary": "Container hashes authenticate inputs; arbitrary corruption is not guaranteed to be an invalid model.",
                "scalar_boundary": "Direct zero-dimensional grammar fixtures do not assert that the NumPy exporter preserves scalar shape.",
                "strict_subset_rejections": ["int4_outside_public_writer_domain", "extent_exceeds_bound", "rope_nonvector_frequency"]}
    for name, tensors in populations.items():
        parent, d, g = [encode_reference(tensors, mode) for mode in ("P", "D", "G")]
        if parent != encode_reference(tensors, "K"):
            raise AssertionError("P/K bookkeeping changed public bytes")
        if name == "zero_tensors" and parent != PARENT_MAGIC + b"\0" * 9:
            raise AssertionError("independent zero-tensor golden differs")
        local = histograms(tensors)
        stream_offset = 77 + 64 * len(local)
        if d[:12] != g[:12] or d[13:stream_offset] != g[13:stream_offset]:
            raise AssertionError("D/G side information differs")
        if name == "heterogeneous_tensors" and d[stream_offset:] == g[stream_offset:]:
            raise AssertionError("heterogeneous control does not distinguish the model")
        represented = sum(prod(t["shape"]) * (1 if t["dtype"] == DT_I8 else 2 if t["dtype"] == DT_BF16 else 4) for t in tensors)
        regenerated = sum(prod(t["shape"]) * 4 for t in tensors if t["encoding"] in (ROPE_SIN, ROPE_COS))
        manifest["valid"].append({
            "id": name, "parent": write_ref(destination, name + ".tfwc2", parent),
            "raw_reference": write_ref(destination, name + ".weights.bin", raw_reference(tensors)),
            "expected_D": write_ref(destination, name + ".D.gfx2mar1", d),
            "expected_G": write_ref(destination, name + ".G.gfx2mar1", g),
            "tensor_count": len(tensors), "tensor_payload_bytes": represented - regenerated,
            "regenerated_rope_bytes": regenerated, "int4_tensor_count": len(local),
            "range_stream_offset": stream_offset, "side_information_bytes": stream_offset - 12,
            "P_K_bytes_identical": True,
            "D_G_side_information_identical_except_mode": True,
            "required": "upstream raw tensor equality; P/K equal parent; D/G equal goldens; separate restores equal parent; fresh repeats equal each arm"})
    for name, (mode, data) in rejection_streams(populations).items():
        manifest["rejection"].append({"id": name, "mode": mode, "input": write_ref(destination, name + ".invalid", data),
                                      "expected_exit": 1, "output_must_be_absent": True, "partial_must_be_absent": True})
    hetero = populations["heterogeneous_tensors"]
    parent = encode_reference(hetero)
    for selected, wrong_mode in (("D", 2), ("G", 1)):
        data = encode_reference(hetero, selected)
        flipped = data[:12] + bytes([wrong_mode]) + data[13:]
        manifest["comparison_controls"].append({
            "id": "wrong_model_" + selected, "mode": "restore",
            "input": write_ref(destination, "wrong_model_" + selected + ".gfx2mar1", flipped),
            "expected_parent_sha256": hashlib.sha256(parent).hexdigest(),
            "required": "exit 1 with no output, or exit 0 with restored bytes unequal to the exact heterogeneous parent; no leftover partial"})
    corrupted = bytearray(parent)
    corrupted[len(corrupted) // 2] ^= 0x20
    manifest["comparison_controls"].append({
        "id": "bit_corruption", "mode": "hash_admission",
        "input": write_ref(destination, "bit_corruption.tfwc2", bytes(corrupted)),
        "expected_parent_sha256": hashlib.sha256(parent).hexdigest(),
        "required": "reject mismatching pinned input hash before invocation; decoder checksum detection is not claimed"})
    sentinel = write_ref(destination, "output.sentinel", b"preserve-existing-output\n")
    reference = next(row["parent"] for row in manifest["valid"] if row["id"] == "heterogeneous_tensors")
    for name, behavior in {
        "preexisting_output": "exit 1; preserve sentinel final bytes; remove only newly created partial",
        "preexisting_partial": "exit 1; preserve sentinel partial bytes; final remains absent",
        "missing_output_directory": "exit 1; no final or partial created",
        "stdout_failure": "redirect stdout to /dev/full; exit 1 with receipt-flush diagnostic; closed model output still equals parent",
    }.items():
        manifest["output_controls"].append({"id": name, "mode": "P", "input": reference, "sentinel": sentinel,
                                            "expected_exit": 1, "required": behavior})
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # Publish the manifest only after every referenced fixture has closed.
    with (destination / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    prepare(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
