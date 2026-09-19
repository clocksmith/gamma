"""Trace geometry and witness coverage are explicit evidence, not inferred scope."""
from dataclasses import dataclass
from pathlib import Path
import struct


@dataclass(frozen=True)
class TraceGeometry:
    fields: tuple[tuple[str, str], ...]
    byte_order: str
    probability_semantics: str
    event_count: int
    boundary_schedule: str
    coverage: str

    def __post_init__(self):
        if self.byte_order not in ("<", ">") or self.event_count < 0:
            raise ValueError("explicit trace byte order and event count required")
        if self.coverage not in {"introduced_state", "protected_parent_observations",
                                 "complete_parent_state", "common_encoder_decoder_projection"}:
            raise ValueError("unknown witness coverage")
        if not self.fields or not self.probability_semantics or not self.boundary_schedule:
            raise ValueError("incomplete trace geometry")

    @property
    def record_bytes(self):
        return struct.calcsize(self.byte_order + "".join(code for _, code in self.fields))


def compare_trace(left: Path, right: Path, geometry: TraceGeometry) -> dict:
    expected = geometry.record_bytes * geometry.event_count
    if left.stat().st_size != expected or right.stat().st_size != expected:
        raise ValueError("trace length differs from declared geometry")
    offset = 0
    with left.open("rb") as a, right.open("rb") as b:
        while block := a.read(1024 * 1024):
            other = b.read(len(block))
            if len(other) != len(block):
                raise ValueError("trace changed during comparison")
            if block != other:
                first = offset + next(i for i, (x, y) in enumerate(zip(block, other)) if x != y)
                return {"equal": False, "first_byte": first, "first_record": first // geometry.record_bytes,
                        "coverage": geometry.coverage}
            offset += len(block)
    return {"equal": True, "bytes": expected, "coverage": geometry.coverage}
