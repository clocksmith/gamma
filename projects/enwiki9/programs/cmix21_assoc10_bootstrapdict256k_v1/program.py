"""BPD-1: decoder-built prefix dictionary over the frozen B2 backend."""

from __future__ import annotations

import collections
import gzip
import os
import pathlib
import stat
import struct
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_MAGIC = b"BPD1\x00"
_PREFIX = 262144
_WORDS = 44515
_extracted_bin: pathlib.Path | None = None


def _extract_binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is not None and _extracted_bin.exists():
        return _extracted_bin
    fd, path = tempfile.mkstemp(prefix="bpd1-cmix-")
    os.close(fd)
    target = pathlib.Path(path)
    with gzip.open(_BIN_GZ, "rb") as source:
        target.write_bytes(source.read())
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _extracted_bin = target
    return target


def _learn(prefix: bytes) -> bytes:
    counts: dict[bytes, int] = collections.defaultdict(int)
    first: dict[bytes, int] = {}
    i = 0
    while i < len(prefix):
        if not (65 <= prefix[i] <= 90 or 97 <= prefix[i] <= 122):
            i += 1
            continue
        start = i
        token = bytearray()
        while i < len(prefix) and (
            65 <= prefix[i] <= 90 or 97 <= prefix[i] <= 122
        ):
            value = prefix[i]
            token.append(value + 32 if 65 <= value <= 90 else value)
            i += 1
        word = bytes(token)
        counts[word] += 1
        first.setdefault(word, start)
    words = sorted(counts, key=lambda word: (-counts[word], first[word], word))
    return b"".join(word + b"\n" for word in words[:_WORDS])


def _run(flag: str, data: bytes, dictionary: bytes | None = None) -> bytes:
    binary = _extract_binary()
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        source = root / "in"
        destination = root / "out"
        source.write_bytes(data)
        command = [str(binary), flag]
        if dictionary is not None:
            dictionary_path = root / "dictionary"
            dictionary_path.write_bytes(dictionary)
            command.append(str(dictionary_path))
        command.extend((str(source), str(destination)))
        subprocess.run(
            command,
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return destination.read_bytes()


def compress(data: bytes) -> bytes:
    prefix = data[:_PREFIX]
    suffix = data[len(prefix) :]
    prefix_archive = _run("-n", prefix) if prefix else b""
    dictionary = _learn(prefix)
    suffix_archive = _run("-t", suffix, dictionary) if suffix else b""
    header = struct.pack(
        ">QIII", len(data), len(prefix), len(prefix_archive), len(suffix_archive)
    )
    return _MAGIC + header + prefix_archive + suffix_archive


def decompress(archive: bytes) -> bytes:
    header_end = len(_MAGIC) + struct.calcsize(">QIII")
    if len(archive) < header_end or archive[: len(_MAGIC)] != _MAGIC:
        raise ValueError("invalid BPD-1 archive")
    total, prefix_size, first_size, second_size = struct.unpack(
        ">QIII", archive[len(_MAGIC) : header_end]
    )
    if prefix_size > total or header_end + first_size + second_size != len(archive):
        raise ValueError("invalid BPD-1 frame")
    first = archive[header_end : header_end + first_size]
    second = archive[header_end + first_size :]
    prefix = _run("-d", first) if first_size else b""
    if len(prefix) != prefix_size:
        raise ValueError("BPD-1 prefix length mismatch")
    dictionary = _learn(prefix)
    suffix = _run("-d", second, dictionary) if second_size else b""
    result = prefix + suffix
    if len(result) != total:
        raise ValueError("BPD-1 total length mismatch")
    return result

