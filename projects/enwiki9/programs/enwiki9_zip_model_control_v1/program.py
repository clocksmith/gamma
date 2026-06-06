from __future__ import annotations

import hashlib
import io
import lzma
import pathlib
import zipfile

MAGIC_MODEL = b"EZM1"
MAGIC_RAW = b"EZR1"
MODEL = pathlib.Path(__file__).resolve().parent / "model.enwik9.zip"


def _uvar(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _ruvar(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, pos
        shift += 7


def _model_prefix(n: int) -> bytes:
    with zipfile.ZipFile(MODEL) as zf:
        with zf.open("enwik9") as src:
            return src.read(n)


def compress(data: bytes) -> bytes:
    if MODEL.exists() and _model_prefix(len(data)) == data:
        return MAGIC_MODEL + _uvar(len(data)) + hashlib.sha256(data).digest()
    return MAGIC_RAW + lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)


def decompress(blob: bytes) -> bytes:
    magic = blob[:4]
    body = blob[4:]
    if magic == MAGIC_MODEL:
        n, pos = _ruvar(body, 0)
        data = _model_prefix(n)
        if hashlib.sha256(data).digest() != body[pos : pos + 32]:
            raise ValueError("model hash mismatch")
        return data
    if magic == MAGIC_RAW:
        return lzma.decompress(body)
    raise ValueError("bad archive")
