"""Build the frozen B2 runtime with flags stored in its compressed closure."""

from __future__ import annotations

import functools
import lzma
import os
import pathlib
import subprocess
import tempfile


_DIR = pathlib.Path(__file__).resolve().parent
_PAYLOAD = _DIR / "source.tar.raw"
_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]


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
    if raw[:4] != b"FCF1" or len(raw) < 6:
        raise ValueError("invalid finite closure frame")
    cursor = 4
    count = int.from_bytes(raw[cursor : cursor + 2], "big")
    cursor += 2
    directory = pathlib.Path(tempfile.mkdtemp(prefix="cmix21-source-"))
    seen = set()
    for _ in range(count):
        if cursor + 6 > len(raw):
            raise ValueError("truncated closure record")
        name_length = int.from_bytes(raw[cursor : cursor + 2], "big")
        data_length = int.from_bytes(raw[cursor + 2 : cursor + 6], "big")
        cursor += 6
        end_name = cursor + name_length
        end_data = end_name + data_length
        if end_data > len(raw):
            raise ValueError("truncated closure payload")
        name = raw[cursor:end_name].decode()
        path = pathlib.PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or name in seen:
            raise ValueError("unsafe source-closure member")
        seen.add(name)
        destination = directory.joinpath(*path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw[end_name:end_data])
        cursor = end_data
    if cursor != len(raw):
        raise ValueError("trailing closure bytes")
    source = directory / "cmix21"
    _restore_dictionary(source / "english.dic")
    flags = (source / ".gamma_lflags").read_text()
    subprocess.run(
        ["make", "-C", str(source), "cmix", "CXX=g++", f"LFLAGS={flags}"],
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
