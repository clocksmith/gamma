from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "enwiki9_shard_container", ROOT / "tools" / "enwiki9_shard_container.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_four_shard_directory_is_44_bytes_and_payloads_roundtrip(tmp_path: Path) -> None:
    archives = []
    for index, payload in enumerate((b"a", b"bc", b"def", b"ghij")):
        path = tmp_path / f"archive-{index}.comp"
        path.write_bytes(payload)
        archives.append(path)
    container = tmp_path / "archive.sharded"

    directory_bytes = MODULE.pack(archives, [11, 22, 33, 44], container)
    rows = MODULE.unpack(container, tmp_path / "unpacked")

    assert directory_bytes == 44
    assert container.stat().st_size == 44 + sum(path.stat().st_size for path in archives)
    assert [row["raw_bytes"] for row in rows] == [11, 22, 33, 44]
    assert [Path(row["path"]).read_bytes() for row in rows] == [
        path.read_bytes() for path in archives
    ]


def test_unpack_rejects_trailing_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "archive.comp"
    archive.write_bytes(b"payload")
    container = tmp_path / "archive.sharded"
    MODULE.pack([archive], [7], container)
    container.write_bytes(container.read_bytes() + b"x")
    try:
        MODULE.unpack(container, tmp_path / "out")
    except ValueError as error:
        assert "trailing bytes" in str(error)
    else:
        raise AssertionError("missing trailing-byte validation")
