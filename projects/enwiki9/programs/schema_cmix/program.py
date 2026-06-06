"""schema_cmix — XML/text typed-stream split with cmix as the back-end.

Same reversibility model as schema_lzma_v1, swapping lzma for the inlined
cmix binary (sibling cmix.bin.gz file). Driver counts both program.py and
cmix.bin.gz against program_size.
"""

from __future__ import annotations

import gzip
import os
import pathlib
import stat
import struct
import subprocess
import tempfile

SENTINEL = b"\x00\x00\xfe\xff"
TEXT_OPEN = b'<text xml:space="preserve">'
TEXT_CLOSE = b"</text>"

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_extracted: pathlib.Path | None = None


def _binary() -> pathlib.Path:
    global _extracted
    if _extracted is not None and _extracted.exists():
        return _extracted
    fd, path = tempfile.mkstemp(prefix="cmix-", suffix=".bin")
    os.close(fd)
    p = pathlib.Path(path)
    with gzip.open(_BIN_GZ, "rb") as src:
        p.write_bytes(src.read())
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _extracted = p
    return p


def _cmix(flag: str, data: bytes) -> bytes:
    binary = _binary()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(binary), flag, src, dst],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def _split(data: bytes) -> tuple[bytes, bytes]:
    if SENTINEL in data:
        return data, b""
    xml_parts: list[bytes] = []
    text_parts: list[bytes] = []
    pos = 0
    while True:
        i = data.find(TEXT_OPEN, pos)
        if i < 0:
            xml_parts.append(data[pos:])
            break
        xml_parts.append(data[pos : i + len(TEXT_OPEN)])
        j = data.find(TEXT_CLOSE, i + len(TEXT_OPEN))
        if j < 0:
            xml_parts.append(data[i + len(TEXT_OPEN):])
            break
        text_parts.append(data[i + len(TEXT_OPEN) : j])
        xml_parts.append(SENTINEL)
        xml_parts.append(TEXT_CLOSE)
        pos = j + len(TEXT_CLOSE)
    return b"".join(xml_parts), SENTINEL.join(text_parts)


def _merge(xml_stream: bytes, text_stream: bytes) -> bytes:
    if SENTINEL not in xml_stream:
        return xml_stream
    blobs = text_stream.split(SENTINEL) if text_stream else []
    out: list[bytes] = []
    pos = 0
    bi = 0
    while True:
        i = xml_stream.find(SENTINEL, pos)
        if i < 0:
            out.append(xml_stream[pos:])
            break
        out.append(xml_stream[pos:i])
        out.append(blobs[bi])
        bi += 1
        pos = i + len(SENTINEL)
    return b"".join(out)


def compress(data: bytes) -> bytes:
    xml_s, text_s = _split(data)
    xml_c = _cmix("-c", xml_s)
    text_c = _cmix("-c", text_s) if text_s else b""
    return struct.pack(">QQ", len(xml_c), len(text_c)) + xml_c + text_c


def decompress(data: bytes) -> bytes:
    xml_len, text_len = struct.unpack(">QQ", data[:16])
    xml_c = data[16 : 16 + xml_len]
    text_c = data[16 + xml_len : 16 + xml_len + text_len]
    xml_s = _cmix("-d", xml_c)
    text_s = _cmix("-d", text_c) if text_c else b""
    return _merge(xml_s, text_s)
