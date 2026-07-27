"""Self-contained compact Bellard-NNCP candidate in its native text domain."""

from __future__ import annotations

import os
import pathlib
import subprocess
import tarfile
import tempfile


_DIR = pathlib.Path(__file__).resolve().parent
_SOURCE_TAR = _DIR / "nncp_cpu_source.tar.xz"
_build_dir: pathlib.Path | None = None


def _binary() -> tuple[pathlib.Path, dict[str, str]]:
    global _build_dir
    if _build_dir is None or not (_build_dir / "nncp").is_file():
        _build_dir = pathlib.Path(tempfile.mkdtemp(prefix="nncp-compact5-build-"))
        with tarfile.open(_SOURCE_TAR, "r:xz") as archive:
            archive.extractall(_build_dir)
        subprocess.run(
            ["make", "-C", str(_build_dir), "-j2"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    env = os.environ.copy()
    prior = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = (
        str(_build_dir) if not prior else f"{_build_dir}:{prior}"
    )
    return _build_dir / "nncp", env


def _run(arguments: list[str], data: bytes) -> bytes:
    binary, env = _binary()
    with tempfile.TemporaryDirectory(prefix="nncp-compact5-run-") as td:
        source = pathlib.Path(td) / "input"
        destination = pathlib.Path(td) / "output"
        source.write_bytes(data)
        subprocess.run(
            [str(binary), *arguments, str(source), str(destination)],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def compress(data: bytes) -> bytes:
    threads = os.environ.get("NNCP_THREADS", "4")
    return _run(
        [
            "--profile",
            "enwik9",
            "--batch_size",
            "1", "-T", "4",
            "--n_layer",
            "5",
            "--d_model",
            "256",
            "--d_inner",
            "768",
            "--preprocess",
            "16384,512",
            "-T",
            threads,
            "c",
        ],
        data,
    )


def decompress(archive: bytes) -> bytes:
    return _run(["d"], archive)
