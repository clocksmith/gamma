"""Frozen model for the NOEMA semantic-boundary hierarchy QH0 oracle.

The module deliberately exposes no constructive compressor.  QH0 measures
whether a parameter-matched recurrent cell benefits specifically from causal
decoder-visible sentence/field boundaries before an integer codec is built.
"""

from __future__ import annotations

import struct
from typing import Any


PATCH_BYTES = 128
BYTE_VOCABULARY = 257
BYTE_EMBEDDING_WIDTH = 32
SUMMARY_WIDTH = 48
LEVEL_COUNT = 2
LEVEL_EMBEDDING_WIDTH = 8
PREFIX_NODES = 255
MODEL_MAGIC = b"NSBH1\0"


def build_model(torch: Any):
    """Build the one-cell model used by every boundary control."""

    nn = torch.nn

    class NoemaSemanticBoundaryHierarchy(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.byte_embedding = nn.Embedding(
                BYTE_VOCABULARY, BYTE_EMBEDDING_WIDTH
            )
            self.leaf_projection = nn.Linear(
                BYTE_EMBEDDING_WIDTH, SUMMARY_WIDTH
            )
            self.level_embedding = nn.Embedding(
                LEVEL_COUNT, LEVEL_EMBEDDING_WIDTH
            )
            self.shared_cell = nn.GRU(
                SUMMARY_WIDTH + LEVEL_EMBEDDING_WIDTH,
                SUMMARY_WIDTH,
                batch_first=True,
            )
            self.node_readout = nn.Linear(SUMMARY_WIDTH, PREFIX_NODES)

        def states(
            self,
            values,
            segment_positions,
            segment_lengths,
            byte_segment,
            byte_offset,
        ):
            batch, segment_count, segment_width = segment_positions.shape
            gathered = torch.gather(
                values,
                1,
                segment_positions.reshape(batch, -1),
            ).reshape(batch, segment_count, segment_width)
            leaves = self.leaf_projection(self.byte_embedding(gathered))

            level_zero = self.level_embedding.weight[0].reshape(1, 1, 1, -1)
            local_input = torch.cat(
                (leaves, level_zero.expand(batch, segment_count, segment_width, -1)),
                dim=-1,
            ).reshape(batch * segment_count, segment_width, -1)
            local_after, _ = self.shared_cell(local_input)
            local_after = local_after.reshape(
                batch, segment_count, segment_width, SUMMARY_WIDTH
            )
            local_before = torch.cat(
                (
                    torch.zeros_like(local_after[:, :, :1, :]),
                    local_after[:, :, :-1, :],
                ),
                dim=2,
            )

            final_offsets = torch.clamp(segment_lengths - 1, min=0)
            final_index = final_offsets.reshape(batch, segment_count, 1, 1).expand(
                -1, -1, 1, SUMMARY_WIDTH
            )
            summaries = torch.gather(local_after, 2, final_index).squeeze(2)

            level_one = self.level_embedding.weight[1].reshape(1, 1, -1)
            upper_input = torch.cat(
                (summaries, level_one.expand(batch, segment_count, -1)), dim=-1
            )
            upper_after, _ = self.shared_cell(upper_input)
            upper_before = torch.cat(
                (torch.zeros_like(upper_after[:, :1, :]), upper_after[:, :-1, :]),
                dim=1,
            )

            local_flat = local_before.reshape(
                batch, segment_count * segment_width, SUMMARY_WIDTH
            )
            local_index = (
                byte_segment * segment_width + byte_offset
            ).unsqueeze(-1).expand(-1, -1, SUMMARY_WIDTH)
            local_state = torch.gather(local_flat, 1, local_index)
            upper_index = byte_segment.unsqueeze(-1).expand(
                -1, -1, SUMMARY_WIDTH
            )
            upper_state = torch.gather(upper_before, 1, upper_index)
            has_upper = (byte_segment > 0).to(local_state.dtype).unsqueeze(-1)
            return (local_state + upper_state) / torch.sqrt(1.0 + has_upper)

        def forward(
            self,
            values,
            segment_positions,
            segment_lengths,
            byte_segment,
            byte_offset,
            *,
            return_states: bool = False,
        ):
            states = self.states(
                values,
                segment_positions,
                segment_lengths,
                byte_segment,
                byte_offset,
            )
            residuals = self.node_readout(states)
            if return_states:
                return residuals, states
            return residuals

    return NoemaSemanticBoundaryHierarchy()


def quantize_model(torch: Any, model: Any) -> tuple[bytes, dict[str, Any]]:
    """Serialize signed-int8 tensors canonically and return reloaded tensors."""

    import numpy as np

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
        dequantized[name] = torch.from_numpy(values.astype(np.float32) * scale)

    output = bytearray(MODEL_MAGIC)
    output += struct.pack("<H", len(quantized))
    for name in sorted(quantized):
        encoded_name = name.encode("ascii")
        values = quantized[name]
        output += struct.pack("<H", len(encoded_name)) + encoded_name
        output += struct.pack("<B", values.ndim)
        for dimension in values.shape:
            output += struct.pack("<I", int(dimension))
        output += struct.pack("<f", float(scales[name]))
        output += values.tobytes(order="C")
    return bytes(output), dequantized


def parameter_count(model: Any) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def compress(_data: bytes) -> bytes:
    raise RuntimeError("QH0 has no constructive compressor until its gate passes")


def decompress(_archive: bytes) -> bytes:
    raise RuntimeError("QH0 has no constructive decoder until its gate passes")
