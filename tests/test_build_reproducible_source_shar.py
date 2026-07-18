from __future__ import annotations

import importlib.util
import subprocess
import zipfile
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "enwiki9"
    / "tools"
    / "build_reproducible_source_shar.py"
)
SPEC = importlib.util.spec_from_file_location("source_shar", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_shar_reconstructs_text_sources(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "src").mkdir(parents=True)
    (root / "Makefile").write_text("all:\n\ttrue\n")
    (root / "src" / "main.cpp").write_text("int main() { return 0; }\n")
    names = ["Makefile", "src/main.cpp"]
    bundle = tmp_path / "source_bundle.sh"
    restored = tmp_path / "restored"
    MODULE.build_shar(root, names, bundle)
    subprocess.run([str(bundle), str(restored)], check=True)
    for name in names:
        assert (restored / name).read_bytes() == (root / name).read_bytes()


def test_shar_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").write_text("alpha\n")
    first = tmp_path / "first.sh"
    second = tmp_path / "second.sh"
    MODULE.build_shar(root, ["a"], first)
    MODULE.build_shar(root, ["a"], second)
    assert first.read_bytes() == second.read_bytes()


def test_delimiter_avoids_payload_line() -> None:
    payload = b"__ENWIKI9_SOURCE_EOF__\nbody\n"
    assert MODULE.delimiter("a", payload) == "__ENWIKI9_SOURCE_EOF_1__"


def test_source_package_is_deterministic_and_reconstructs(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "Makefile").write_text("all:\n\ttrue\n")
    bundle = tmp_path / "source_bundle.sh"
    MODULE.build_shar(root, ["Makefile"], bundle)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    MODULE.build_package(bundle, first)
    MODULE.build_package(bundle, second)
    assert first.read_bytes() == second.read_bytes()

    extracted = tmp_path / "package"
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == ["Makefile", "source_bundle.sh"]
        assert archive.testzip() is None
        archive.extractall(extracted)
    restored = tmp_path / "restored"
    subprocess.run(
        ["sh", str(extracted / "source_bundle.sh"), str(restored)], check=True
    )
    assert (restored / "Makefile").read_bytes() == (root / "Makefile").read_bytes()
