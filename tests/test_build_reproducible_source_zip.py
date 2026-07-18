from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "enwiki9"
    / "tools"
    / "build_reproducible_source_zip.py"
)
SPEC = importlib.util.spec_from_file_location("source_zip", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_zip_is_deterministic_and_direct(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "Makefile").write_text("all:\n\ttrue\n")
    (root / "source.cpp").write_text("int main() { return 0; }\n")
    names = ["Makefile", "source.cpp"]
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    MODULE.build_zip(root, names, first, zipfile.ZIP_LZMA)
    MODULE.build_zip(root, names, second, zipfile.ZIP_LZMA)
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == names
        assert archive.testzip() is None


def test_source_names_rejects_parent_path(tmp_path: Path) -> None:
    file_list = tmp_path / "files"
    file_list.write_text("../secret\n")
    try:
        MODULE.source_names(file_list)
    except ValueError as error:
        assert "unsafe" in str(error)
    else:
        raise AssertionError("unsafe path was accepted")
