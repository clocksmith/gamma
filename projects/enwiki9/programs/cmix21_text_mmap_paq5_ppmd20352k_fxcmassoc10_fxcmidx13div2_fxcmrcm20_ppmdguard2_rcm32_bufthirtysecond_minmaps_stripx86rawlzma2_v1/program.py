"""Self-contained B2 candidate with an x86-filtered solid LZMA2 payload."""

from __future__ import annotations

import functools
import lzma
import os
import pathlib
import subprocess
import tempfile


_DIR = pathlib.Path(__file__).resolve().parent
_PAYLOAD = _DIR / "payload.bin.raw"
_EXECUTABLE_BYTES = 722_448
_PAYLOAD_BYTES = 1_134_444
_FILTERS = [
    {"id": lzma.FILTER_X86},
    {"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME},
]


@functools.lru_cache(maxsize=1)
def _runtime() -> tuple[pathlib.Path, pathlib.Path]:
    payload = lzma.decompress(
        _PAYLOAD.read_bytes(), format=lzma.FORMAT_RAW, filters=_FILTERS
    )
    if len(payload) != _PAYLOAD_BYTES:
        raise ValueError("filtered runtime payload length mismatch")
    directory = pathlib.Path(tempfile.mkdtemp(prefix="cmix21-x86-"))
    binary = directory / "cmix"
    dictionary = directory / "english.dic"
    binary.write_bytes(payload[:_EXECUTABLE_BYTES])
    dictionary.write_bytes(payload[_EXECUTABLE_BYTES:])
    os.chmod(binary, 0o755)
    return binary, dictionary


def _run(data: bytes) -> bytes:
    binary, dictionary = _runtime()
    with tempfile.TemporaryDirectory(prefix="cmix21-x86-run-") as td:
        source = pathlib.Path(td) / "input"
        destination = pathlib.Path(td) / "output"
        source.write_bytes(data)
        subprocess.run(
            [str(binary), "-t", str(dictionary), str(source), str(destination)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def compress(data: bytes) -> bytes:
    return _run(data)


def decompress(archive: bytes) -> bytes:
    return _run(archive)
