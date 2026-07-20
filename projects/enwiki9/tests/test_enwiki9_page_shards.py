from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SPEC = importlib.util.spec_from_file_location(
    "enwiki9_page_shards", TOOLS / "enwiki9_page_shards.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_boundaries_are_deterministic_page_starts() -> None:
    data = b"head" + b"<page>aaa" + b"<page>bbbb" + b"<page>ccccc" + b"tail"
    boundaries = MODULE.choose_boundaries(data, 3)
    assert boundaries == [0, 13, 23, len(data)]
    assert all(data[offset:].startswith(b"<page>") for offset in boundaries[1:-1])


def test_shards_reconstruct_input_exactly(tmp_path: Path) -> None:
    data = b"prefix" + b"<page>a" + b"<page>bb" + b"<page>ccc" + b"suffix"
    input_path = tmp_path / "input.raw"
    input_path.write_bytes(data)
    output_dir = tmp_path / "shards"
    manifest = MODULE.build_shards(input_path, output_dir, 4)
    reconstructed = b"".join(
        Path(row["path"]).read_bytes() for row in manifest["shards"]
    )
    assert reconstructed == data
    assert manifest["reconstruction"]["exact"] is True


def test_rejects_more_shards_than_page_boundaries() -> None:
    try:
        MODULE.choose_boundaries(b"head<page>one", 3)
    except ValueError as error:
        assert "not enough page boundaries" in str(error)
    else:
        raise AssertionError("missing boundary validation")
