from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "enwiki9"
    / "tools"
    / "seal_wrt_static_boundary_swap_geometry_title_proxy.py"
)
SPEC = importlib.util.spec_from_file_location("boundary_proxy", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_compressed_size_is_deterministic(tmp_path: Path) -> None:
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"abcabcabc" * 100)
    first = MODULE.compressed_size(["gzip", "-9n", "-c"], payload)
    second = MODULE.compressed_size(["gzip", "-9n", "-c"], payload)
    assert first == second
    assert first > 0


def test_sha256_reads_file(tmp_path: Path) -> None:
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"abc")
    assert MODULE.sha256(payload) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
