"""yellow_tucan_numeric_cmix_v1.

Reversible numeric semantic coding followed by cmix. Conservative markers
cover ISO dates, standalone years, and medium-size unsigned decimal integers.

The cmix binary is vendored as sibling `cmix.bin.gz`; the harness counts it
in program_size.
"""

from __future__ import annotations

import datetime as _dt
import gzip
import os
import re
import pathlib
import stat
import subprocess
import tempfile

ESC = 0x11
TAG_LITERAL_ESC = 0x00
TAG_DATE = 0x01
TAG_YEAR = 0x02
TAG_UINT = 0x03
EPOCH = _dt.date(1500, 1, 1)

NUM_RE = re.compile(
    rb"(?P<date>(?<![0-9A-Za-z])(?:1[5-9]|20|21)[0-9]{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])(?![0-9A-Za-z]))"
    rb"|(?P<year>(?<![0-9A-Za-z])(?:1[5-9]|20|21)[0-9]{2}(?![0-9A-Za-z]))"
    rb"|(?P<uint>(?<![0-9A-Za-z])[1-9][0-9]{4,15}(?![0-9A-Za-z]))"
)

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


def _date_payload(raw: bytes) -> bytes | None:
    y = int(raw[0:4])
    m = int(raw[5:7])
    d = int(raw[8:10])
    try:
        delta = (_dt.date(y, m, d) - EPOCH).days
    except ValueError:
        return None
    if 0 <= delta < (1 << 24):
        return delta.to_bytes(3, "big")
    return None


def _encode(data: bytes) -> bytes:
    parts: list[bytes] = []
    pos = 0
    date_count = 0
    year_count = 0
    uint_count = 0
    numeric_source_bytes = 0
    for m in NUM_RE.finditer(data):
        raw = m.group(0)
        parts.append(_double_esc(data[pos : m.start()]))
        if m.group("date") is not None:
            payload = _date_payload(raw)
            if payload is None:
                parts.append(_double_esc(raw))
            else:
                parts.append(bytes([ESC, TAG_DATE]) + payload)
                date_count += 1
                numeric_source_bytes += len(raw)
        elif m.group("year") is not None:
            year = int(raw)
            parts.append(bytes([ESC, TAG_YEAR]) + (year - 1500).to_bytes(2, "big"))
            year_count += 1
            numeric_source_bytes += len(raw)
        else:
            value = int(raw)
            payload = _varint(value)
            encoded = bytes([ESC, TAG_UINT]) + payload
            if len(encoded) < len(raw):
                parts.append(encoded)
                uint_count += 1
                numeric_source_bytes += len(raw)
            else:
                parts.append(_double_esc(raw))
        pos = m.end()
    parts.append(_double_esc(data[pos:]))
    encoded = b"".join(parts)
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "transformed_size": len(encoded),
            "numeric_source_bytes": numeric_source_bytes,
            "date_count": date_count,
            "year_count": year_count,
            "uint_count": uint_count,
        }
    )
    return encoded


def _decode(stream: bytes) -> bytes:
    out: list[bytes] = []
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
            raise ValueError("trailing numeric ESC")
        tag = stream[pos]
        pos += 1
        if tag == TAG_LITERAL_ESC:
            out.append(bytes([ESC]))
        elif tag == TAG_DATE:
            payload = stream[pos : pos + 3]
            if len(payload) != 3:
                raise ValueError("truncated date")
            pos += 3
            date = EPOCH + _dt.timedelta(days=int.from_bytes(payload, "big"))
            out.append(f"{date.year:04d}-{date.month:02d}-{date.day:02d}".encode())
        elif tag == TAG_YEAR:
            payload = stream[pos : pos + 2]
            if len(payload) != 2:
                raise ValueError("truncated year")
            pos += 2
            out.append(str(1500 + int.from_bytes(payload, "big")).encode())
        elif tag == TAG_UINT:
            value, pos = _read_varint(stream, pos)
            out.append(str(value).encode())
        else:
            raise ValueError(f"bad numeric tag {tag:#x}")
    return b"".join(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode(data))


def decompress(data: bytes) -> bytes:
    return _decode(_cmix("-d", data))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
