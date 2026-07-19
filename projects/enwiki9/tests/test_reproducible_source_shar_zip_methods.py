from __future__ import annotations

from pathlib import Path
import tempfile
import zipfile

from projects.enwiki9.tools.build_reproducible_source_shar import build_package
from projects.enwiki9.tools.seal_reproducible_source_shar_package import inspect_zip


def test_lzma_source_package_is_deterministic_and_declared() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        bundle = root / "source_bundle.sh"
        package_a = root / "a.zip"
        package_b = root / "b.zip"
        bundle.write_text("#!/bin/sh\nprintf test\\n\n")

        build_package(bundle, package_a, zip_method="lzma")
        build_package(bundle, package_b, zip_method="lzma")

        assert package_a.read_bytes() == package_b.read_bytes()
        audit = inspect_zip(package_a, expected_method="lzma")
        assert audit["all_entries_expected_method"] is True
        assert audit["all_entries_bzip2"] is False
        assert audit["compression_method"] == "lzma"
        with zipfile.ZipFile(package_a) as archive:
            assert archive.testzip() is None
