"""Frozen model definition for the NOEMA binary-carry QH0 oracle.

This is a zero-credit trace candidate.  The final compressor/decompressor is
intentionally not materialized unless the hierarchy-specific headroom gate
passes.  The oracle imports the model and canonical serializer below.
"""

from __future__ import annotations

import math
import struct
from typing import Any


PATCH_BYTES = 128
BYTE_VOCABULARY = 257
BYTE_EMBEDDING_WIDTH = 32
SUMMARY_WIDTH = 48
LEVEL_COUNT = 7
LEVEL_EMBEDDING_WIDTH = 8
PREFIX_NODES = 255
MODEL_MAGIC = b"NMDL1\0"
MODEL_MODES = {"flat": 1, "hierarchy": 2}


def build_model(torch: Any, mode: str):
    """Build N1 or N2 with matched tensor shapes and parameter counts."""

    if mode not in MODEL_MODES:
        raise ValueError(f"unknown NOEMA model mode: {mode}")
    nn = torch.nn

    class NoemaBinaryCarry(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.mode = mode
            self.byte_embedding = nn.Embedding(
                BYTE_VOCABULARY, BYTE_EMBEDDING_WIDTH
            )
            self.leaf_projection = nn.Linear(
                BYTE_EMBEDDING_WIDTH, SUMMARY_WIDTH
            )
            self.level_embedding = nn.Embedding(
                LEVEL_COUNT, LEVEL_EMBEDDING_WIDTH
            )
            if mode == "flat":
                self.shared_cell = nn.GRU(
                    SUMMARY_WIDTH + LEVEL_EMBEDDING_WIDTH,
                    SUMMARY_WIDTH,
                    batch_first=True,
                )
            else:
                self.shared_cell = nn.GRUCell(
                    SUMMARY_WIDTH + LEVEL_EMBEDDING_WIDTH,
                    SUMMARY_WIDTH,
                )
            self.node_readout = nn.Linear(SUMMARY_WIDTH, PREFIX_NODES)

        def _leaves(self, values):
            return self.leaf_projection(self.byte_embedding(values))

        def _flat_states(self, leaves):
            batch, length, _width = leaves.shape
            level_zero = self.level_embedding.weight[0].reshape(1, 1, -1)
            levels = level_zero.expand(batch, length, -1)
            inputs = torch.cat((leaves, levels), dim=-1)
            after, _final = self.shared_cell(inputs)
            zero = torch.zeros(
                (batch, 1, SUMMARY_WIDTH),
                dtype=after.dtype,
                device=after.device,
            )
            return torch.cat((zero, after[:, :-1, :]), dim=1)

        def _hierarchy_states(self, leaves):
            if leaves.shape[1] != PATCH_BYTES:
                raise ValueError(
                    f"hierarchy requires {PATCH_BYTES} bytes per patch"
                )
            summaries = [leaves]
            current = leaves
            for level in range(LEVEL_COUNT):
                left = current[:, 0::2, :]
                right = current[:, 1::2, :]
                embedding = self.level_embedding.weight[level].reshape(1, 1, -1)
                embedding = embedding.expand(
                    right.shape[0], right.shape[1], -1
                )
                inputs = torch.cat((right, embedding), dim=-1)
                merged = self.shared_cell(
                    inputs.reshape(-1, inputs.shape[-1]),
                    left.reshape(-1, left.shape[-1]),
                ).reshape(left.shape)
                summaries.append(merged)
                current = merged

            positions = torch.arange(PATCH_BYTES, device=leaves.device)
            aggregate = torch.zeros_like(leaves)
            counts = torch.zeros(
                PATCH_BYTES, dtype=leaves.dtype, device=leaves.device
            )
            for level in range(LEVEL_COUNT):
                active = ((positions >> level) & 1).to(leaves.dtype)
                indices = (positions >> (level + 1)) << 1
                contribution = summaries[level][:, indices, :]
                aggregate = aggregate + contribution * active.reshape(1, -1, 1)
                counts = counts + active
            divisor = torch.sqrt(torch.clamp(counts, min=1.0)).reshape(1, -1, 1)
            return aggregate / divisor

        def states(self, values):
            leaves = self._leaves(values)
            if self.mode == "flat":
                return self._flat_states(leaves)
            return self._hierarchy_states(leaves)

        def forward(self, values, *, return_states: bool = False):
            states = self.states(values)
            residuals = self.node_readout(states)
            if return_states:
                return residuals, states
            return residuals

        def readout_states(self, states):
            return self.node_readout(states)

    return NoemaBinaryCarry()


def quantize_model(torch: Any, model: Any, mode: str):
    """Return canonical int8 bytes and the corresponding float32 state."""

    import numpy as np

    if mode not in MODEL_MODES:
        raise ValueError(f"unknown NOEMA model mode: {mode}")
    quantized: dict[str, Any] = {}
    scales: dict[str, Any] = {}
    dequantized: dict[str, Any] = {}
    for name, tensor in sorted(model.state_dict().items()):
        array = tensor.detach().cpu().numpy().astype(np.float32)
        maximum = float(np.max(np.abs(array))) if array.size else 0.0
        scale = np.float32(maximum / 127.0 if maximum > 0.0 else 1.0)
        values = np.clip(np.rint(array / scale), -127, 127).astype(np.int8)
        quantized[name] = values
        scales[name] = scale
        dequantized[name] = torch.from_numpy(
            values.astype(np.float32) * scale
        )

    output = bytearray(MODEL_MAGIC)
    output += struct.pack("<BH", MODEL_MODES[mode], len(quantized))
    for name in sorted(quantized):
        encoded_name = name.encode("ascii")
        values = quantized[name]
        output += struct.pack("<H", len(encoded_name))
        output += encoded_name
        output += struct.pack("<B", values.ndim)
        for dimension in values.shape:
            output += struct.pack("<I", int(dimension))
        output += struct.pack("<f", float(scales[name]))
        output += values.tobytes(order="C")
    return bytes(output), dequantized


def parameter_count(model: Any) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def expected_parameter_count() -> int:
    embedding = BYTE_VOCABULARY * BYTE_EMBEDDING_WIDTH
    leaf = BYTE_EMBEDDING_WIDTH * SUMMARY_WIDTH + SUMMARY_WIDTH
    levels = LEVEL_COUNT * LEVEL_EMBEDDING_WIDTH
    cell = (
        3 * SUMMARY_WIDTH * (SUMMARY_WIDTH + LEVEL_EMBEDDING_WIDTH)
        + 3 * SUMMARY_WIDTH * SUMMARY_WIDTH
        + 6 * SUMMARY_WIDTH
    )
    readout = SUMMARY_WIDTH * PREFIX_NODES + PREFIX_NODES
    return embedding + leaf + levels + cell + readout


def compress(_data: bytes) -> bytes:
    raise RuntimeError(
        "QH0 is a zero-credit trace oracle; compressor construction requires a pass"
    )


def decompress(_archive: bytes) -> bytes:
    raise RuntimeError(
        "QH0 is a zero-credit trace oracle; decoder construction requires a pass"
    )
