from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import struct
import sys


TOOLS = Path(__file__).resolve().parents[1] / "projects/enwiki9/tools"


def load(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PAIRED = load("endpoint428_paired_trace")
AUTOMATON = load("wrt_title_token_automaton")


def make_pair(path: Path, rows: list[tuple[int, int, int, int]]) -> None:
    path.write_bytes(
        PAIRED.PAIR_HEADER.pack(
            PAIRED.PAIR_MAGIC,
            PAIRED.PAIR_VERSION,
            PAIRED.PAIR_HEADER_BYTES,
            PAIRED.PAIR_ROW_BYTES,
            PAIRED.PAIR_FIELD_MASK,
            len(rows),
        )
        + b"".join(struct.pack("<HHHB", *row) for row in rows)
    )


def test_paired_trace_validates_and_materializes_hybrid(tmp_path: Path) -> None:
    bits = (1, 0, 1, 1, 0, 0, 1, 0)
    rows = [
        (30_000 + index, 40_000 - index, 35_000 + index, bit)
        for index, bit in enumerate(bits)
    ]
    paired = tmp_path / "paired.bin"
    final_p1 = tmp_path / "final.p1"
    archive_on = tmp_path / "archive_on.bin"
    archive_off = tmp_path / "archive_off.bin"
    raw = tmp_path / "input.raw"
    restored = tmp_path / "restored.raw"
    output = tmp_path / "hybrid.trace"
    make_pair(paired, rows)
    final_p1.write_bytes(
        b"CMX21P1\0"
        + len(rows).to_bytes(8, "little")
        + b"".join(row[2].to_bytes(2, "little") for row in rows)
    )
    counter = PAIRED.RangeCounter()
    for _base, _endpoint, hybrid, bit in rows:
        counter.encode(bit, hybrid)
    counter.finish()
    archive_on.write_bytes(b"\0\0\0\0\1" + bytes(counter.bytes))
    archive_off.write_bytes(archive_on.read_bytes())
    raw.write_bytes(b"same")
    restored.write_bytes(raw.read_bytes())

    receipt = PAIRED.materialize(
        paired,
        output,
        final_p1_path=final_p1,
        archive_path=archive_on,
        trace_off_archive_path=archive_off,
        input_path=raw,
        restored_path=restored,
        state_origin="cold_reset_window",
        scope_bytes=4,
        chunk_rows=3,
    )

    traced = list(AUTOMATON.iter_trace_bytes(output))
    assert receipt["accepted"] is True
    assert receipt["identity"] == {
        "probabilities_valid": True,
        "truth_valid": True,
        "final_rows_match": True,
        "hybrid_equals_final_p1": True,
        "trace_on_off_archive_identical": True,
        "hybrid_range_payload_match": True,
        "archive_wrt_length_match": True,
        "roundtrip_ok": True,
        "identity_complete": True,
    }
    assert [row.value for row in traced] == [0b10110010]
    assert traced[0].probabilities == tuple(row[2] for row in rows)
    assert receipt["wrt_sha256"] == hashlib.sha256(bytes((0b10110010,))).hexdigest()


def test_paired_trace_rejects_mismatched_final_stream(tmp_path: Path) -> None:
    rows = [(30_000, 40_000, 35_000, bit) for bit in (1, 0, 1, 0, 1, 0, 1, 0)]
    paired = tmp_path / "paired.bin"
    final_p1 = tmp_path / "final.p1"
    output = tmp_path / "hybrid.trace"
    make_pair(paired, rows)
    final_p1.write_bytes(
        b"CMX21P1\0" + len(rows).to_bytes(8, "little") + (35_001).to_bytes(2, "little") * len(rows)
    )

    receipt = PAIRED.materialize(
        paired,
        output,
        final_p1_path=final_p1,
        state_origin="cold_reset_window",
        scope_bytes=1,
    )

    assert receipt["accepted"] is False
    assert receipt["identity"]["hybrid_equals_final_p1"] is False
    assert receipt["identity"]["identity_complete"] is False
