"""Self-contained CPU NNCP codec with the exact midpoint update schedule."""

from __future__ import annotations

import lzma
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile


_DIR = Path(__file__).resolve().parent
_SOURCE_TAR = _DIR / "nncp_cpu_source.tar.xz"
_PATCH_XZ = _DIR / "nncp_midsegment32.patch.xz"
_build_dir: Path | None = None


def _binary() -> tuple[Path, dict[str, str]]:
    global _build_dir
    if _build_dir is None or not (_build_dir / "nncp").is_file():
        configured = os.environ.get("NNCP_BUILD_DIR")
        if configured:
            _build_dir = Path(configured)
            _build_dir.mkdir(parents=True, exist_ok=False)
        else:
            _build_dir = Path(tempfile.mkdtemp(prefix="nncp-midpoint-build-"))
        with tarfile.open(_SOURCE_TAR, "r:xz") as archive:
            archive.extractall(_build_dir)
        subprocess.run(
            ["make", "-j4"],
            cwd=_build_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        patch_path = _build_dir / "midpoint.patch"
        patch_path.write_bytes(lzma.decompress(_PATCH_XZ.read_bytes()))
        subprocess.run(
            ["patch", "-s", "-p1", "-i", str(patch_path)],
            cwd=_build_dir,
            check=True,
        )
        subprocess.run(
            ["make", "-j4"],
            cwd=_build_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    environment = os.environ.copy()
    prior = environment.get("LD_LIBRARY_PATH")
    environment["LD_LIBRARY_PATH"] = (
        str(_build_dir) if not prior else f"{_build_dir}:{prior}"
    )
    return _build_dir / "nncp", environment


def _run(arguments: list[str], data: bytes) -> bytes:
    binary, environment = _binary()
    with tempfile.TemporaryDirectory(prefix="nncp-midpoint-run-") as temp:
        source = Path(temp) / "input"
        destination = Path(temp) / "output"
        source.write_bytes(data)
        subprocess.run(
            [str(binary), *arguments, str(source), str(destination)],
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def compress(data: bytes) -> bytes:
    threads = os.environ.get("NNCP_THREADS", "4")
    return _run(
        [
            "-q",
            "-T",
            threads,
            "--profile",
            "enwik9",
            "--midsegment32",
            "--preprocess",
            "16384,512",
            "c",
        ],
        data,
    )


def decompress(archive: bytes) -> bytes:
    threads = os.environ.get("NNCP_THREADS", "4")
    return _run(["-q", "-T", threads, "d"], archive)
