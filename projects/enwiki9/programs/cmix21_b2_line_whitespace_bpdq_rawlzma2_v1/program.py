"""Build the frozen B2 cmix21 runtime from a compressed source closure."""

from __future__ import annotations

import functools
import io
import lzma
import os
import pathlib
import subprocess
import tarfile
import tempfile


_DIR = pathlib.Path(__file__).resolve().parent
_PAYLOAD = _DIR / "source.tar.raw"
_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
_FLAGS = (
    "-std=c++14 -Wall -O3 "
    "-DCMIX_PAQ8_LEVEL=5 "
    "-DCMIX_PPMD_MEMORY_MB=21 -DCMIX_PPMD_MEMORY_KB=20352 "
    "-DCMIX_PAQ8_MAIN_CONTEXT_SCALE=1 -DCMIX_PAQ8_MAIN_CONTEXT_DIV=1 "
    "-DCMIX_PAQ8_TEXT_MODEL_SCALE=1 -DCMIX_PAQ8_TEXT_MODEL_DIV=1 "
    "-DCMIX_PAQ8_MATCH_SCALE=1 -DCMIX_PAQ8_MATCH_DIV=1 "
    "-DCMIX_PAQ8_SPARSE_MATCH_DIV=8 -DCMIX_PAQ8_RCM_DIV=32 "
    "-DCMIX_PAQ8_BUF_SCALE=1 -DCMIX_PAQ8_BUF_DIV=32 "
    "-DCMIX_FXCM_CMC2_DIV=1 -DCMIX_FXCM_RCM_DIV=20 "
    "-DCMIX_FXCM_MHASH_DIV=1 -DCMIX_FXCM_CMC2_IDX13_DIV=2 "
    "-DCMIX_FXCM_CMC2_ASSOC=10"
)


def _restore_dictionary(path: pathlib.Path) -> None:
    data = path.read_bytes()
    if data[:4] != b"BPD1" or len(data) < 5 or data[4] not in (0, 1):
        raise ValueError("invalid bounded-prefix dictionary")
    previous = b""
    words = []
    for record in data[5:].splitlines():
        if not record:
            raise ValueError("invalid bounded-prefix record")
        lcp = record[0] - 32
        if lcp < 0 or lcp > len(previous):
            raise ValueError("invalid bounded-prefix length")
        previous = previous[:lcp] + record[1:]
        words.append(previous)
    path.write_bytes(b"\n".join(words) + (b"\n" if data[4] else b""))


@functools.lru_cache(maxsize=1)
def _runtime() -> tuple[pathlib.Path, pathlib.Path]:
    raw = lzma.decompress(
        _PAYLOAD.read_bytes(), format=lzma.FORMAT_RAW, filters=_FILTERS
    )
    directory = pathlib.Path(tempfile.mkdtemp(prefix="cmix21-source-"))
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ValueError("unsafe source-closure member")
        archive.extractall(directory)
    source = directory / "cmix21"
    _restore_dictionary(source / "english.dic")
    subprocess.run(
        ["make", "-C", str(source), "cmix", "CXX=g++", f"LFLAGS={_FLAGS}"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return source / "cmix", source / "english.dic"


def _run(data: bytes, mode: str) -> bytes:
    binary, dictionary = _runtime()
    with tempfile.TemporaryDirectory(prefix="cmix21-source-run-") as td_raw:
        directory = pathlib.Path(td_raw)
        source = directory / "input"
        destination = directory / "output"
        source.write_bytes(data)
        environment = os.environ.copy()
        environment.setdefault("CMIX_MMAP_ALLOC", "1")
        environment.setdefault("CMIX_MMAP_DIR", str(directory))
        subprocess.run(
            [str(binary), mode, str(dictionary), str(source), str(destination)],
            cwd=directory,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def compress(data: bytes) -> bytes:
    return _run(data, "-t")


def decompress(archive: bytes) -> bytes:
    return _run(archive, "-d")
