from __future__ import annotations

import importlib.util
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_TOOL = ROOT / "projects/enwiki9/tools/build_reproducible_source_shar.py"
SEAL_TOOL = ROOT / "projects/enwiki9/tools/seal_reproducible_source_shar_package.py"
SPEC = importlib.util.spec_from_file_location("source_package_seal", SEAL_TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_inspect_zip_requires_direct_bzip2_entries(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "english.dic").write_text("word\n")
    names = tmp_path / "files.list"
    names.write_text("english.dic\n")
    bundle = tmp_path / "source_bundle.sh"
    package = tmp_path / "source.zip"
    subprocess.run(
        [
            "python3",
            str(BUILD_TOOL),
            "--root",
            str(source),
            "--file-list",
            str(names),
            "--output",
            str(bundle),
            "--package-zip",
            str(package),
        ],
        check=True,
    )
    evidence = MODULE.inspect_zip(package)
    assert evidence["entries"] == ["Makefile", "source_bundle.sh"]
    assert evidence["direct_entries_ok"]
    assert evidence["integrity_ok"]
    assert evidence["all_entries_bzip2"]
    assert evidence["comment_bytes"] == 0
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None


def test_verify_reconstruction_detects_identity(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "english.dic").write_text("word\n")
    names = tmp_path / "files.list"
    names.write_text("english.dic\n")
    bundle = tmp_path / "source_bundle.sh"
    package = tmp_path / "source.zip"
    subprocess.run(
        [
            "python3",
            str(BUILD_TOOL),
            "--root",
            str(source),
            "--file-list",
            str(names),
            "--output",
            str(bundle),
            "--package-zip",
            str(package),
        ],
        check=True,
    )
    assert MODULE.verify_reconstruction(
        root=source, names=["english.dic"], source_zip=package
    ) == (True, "")


def test_clean_build_argument_names_are_frozen() -> None:
    source = SEAL_TOOL.read_text()
    for name in (
        "--clean-backend-a",
        "--clean-backend-b",
        "--clean-program-a",
        "--clean-program-b",
        "--reference-backend",
    ):
        assert name in source
