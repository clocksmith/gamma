"""yellow_tucan_title_table_cmix_v1.

Online reversible table for wiki links followed by cmix. This tests whether
entity self-reference helps cmix, after title_table_v1 lost under lzma.

The cmix binary is vendored as sibling `cmix.bin.gz`; the harness counts it
in program_size.
"""

from __future__ import annotations

import gzip
import os
import re
import pathlib
import stat
import subprocess
import tempfile

LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")

ESC = 0x10
TAG_LITERAL_ESC = 0x00
TAG_NEW = 0x01
TAG_REF = 0x02
TAG_REF_ALT = 0x03

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_extracted: pathlib.Path | None = None
LAST_STATS: dict[str, int] = {}


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


def _varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    n = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint too large")


def _double_esc(chunk: bytes) -> bytes:
    return chunk.replace(bytes([ESC]), bytes([ESC, TAG_LITERAL_ESC]))


def _encode(data: bytes) -> bytes:
    out: list[bytes] = []
    vocab: dict[bytes, int] = {}
    pos = 0
    new_count = 0
    ref_count = 0
    alt_count = 0
    source_link_bytes = 0
    for m in LINK_RE.finditer(data):
        out.append(_double_esc(data[pos : m.start()]))
        title = m.group(1)
        alt = m.group(3)
        source_link_bytes += m.end() - m.start()
        idx = vocab.get(title)
        if idx is None:
            vocab[title] = len(vocab)
            new_count += 1
            out.append(bytes([ESC, TAG_NEW]) + _varint(len(title)) + title)
            if alt is None:
                out.append(b"\x00")
            else:
                alt_count += 1
                out.append(b"\x01" + _varint(len(alt)) + alt)
        elif alt is None:
            ref_count += 1
            out.append(bytes([ESC, TAG_REF]) + _varint(idx))
        else:
            ref_count += 1
            alt_count += 1
            out.append(bytes([ESC, TAG_REF_ALT]) + _varint(idx) + _varint(len(alt)) + alt)
        pos = m.end()
    out.append(_double_esc(data[pos:]))
    encoded = b"".join(out)
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "transformed_size": len(encoded),
            "link_source_bytes": source_link_bytes,
            "link_vocab_size": len(vocab),
            "link_new_count": new_count,
            "link_ref_count": ref_count,
            "link_alt_count": alt_count,
        }
    )
    return encoded


def _decode(stream: bytes) -> bytes:
    out: list[bytes] = []
    vocab: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        i = stream.find(bytes([ESC]), pos)
        if i < 0:
            out.append(stream[pos:])
            break
        out.append(stream[pos:i])
        pos = i + 1
        if pos >= n:
            raise ValueError("trailing ESC")
        tag = stream[pos]
        pos += 1
        if tag == TAG_LITERAL_ESC:
            out.append(bytes([ESC]))
        elif tag == TAG_NEW:
            ln, pos = _read_varint(stream, pos)
            title = stream[pos : pos + ln]
            if len(title) != ln:
                raise ValueError("truncated title")
            pos += ln
            vocab.append(title)
            if pos >= n:
                raise ValueError("truncated alt flag")
            has_alt = stream[pos]
            pos += 1
            if has_alt == 0:
                out.append(b"[[" + title + b"]]")
            elif has_alt == 1:
                ln2, pos = _read_varint(stream, pos)
                alt = stream[pos : pos + ln2]
                if len(alt) != ln2:
                    raise ValueError("truncated alt")
                pos += ln2
                out.append(b"[[" + title + b"|" + alt + b"]]")
            else:
                raise ValueError(f"bad alt flag {has_alt}")
        elif tag == TAG_REF:
            idx, pos = _read_varint(stream, pos)
            out.append(b"[[" + vocab[idx] + b"]]")
        elif tag == TAG_REF_ALT:
            idx, pos = _read_varint(stream, pos)
            ln2, pos = _read_varint(stream, pos)
            alt = stream[pos : pos + ln2]
            if len(alt) != ln2:
                raise ValueError("truncated ref alt")
            pos += ln2
            out.append(b"[[" + vocab[idx] + b"|" + alt + b"]]")
        else:
            raise ValueError(f"bad title tag {tag:#x}")
    return b"".join(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode(data))


def decompress(data: bytes) -> bytes:
    return _decode(_cmix("-d", data))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
