"""purple_parrot_numeric_cmix_v1 — semantic ISO-date encoding preprocessor
on top of cmix as the back-end.

Layer 1: identical to numeric_v1's bug-fixed encoder. Conservative — only
ISO 8601 dates between 1500-01-01 and 2199-12-31. Each becomes a 3-byte
days-since-1500 integer wrapped in a 2-byte marker `0x11 0xff`. Literal
0x11 in payload is escape-doubled to `0x11 0x00`.

Layer 2: cmix as the back-end via subprocess.

Architecture test: numeric_v1 was theorized to gain ~0.5-1.5% but cmix
already has internal numeric models. This program measures whether the
explicit semantic encoding adds value on top of cmix's preemption.

Score-honesty caveat: cmix binary is NOT inlined here.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
import subprocess
import tempfile

ISO_DATE_RE = re.compile(
    rb"(?<![0-9])((?:1[5-9]|20|21)[0-9]{2})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(?![0-9])"
)

ESC = 0x11
DATE_TAG = 0xFF
EPOCH = _dt.date(1500, 1, 1)

_CMIX = shutil.which("cmix")


def _require_cmix() -> str:
    if _CMIX is None:
        raise RuntimeError(
            "cmix not on PATH; install from https://github.com/byronknoll/cmix"
        )
    return _CMIX


def _cmix(flag: str, data: bytes) -> bytes:
    binary = _require_cmix()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [binary, flag, src, dst],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def _encode_date(y: int, m: int, d: int) -> bytes | None:
    try:
        delta = (_dt.date(y, m, d) - EPOCH).days
    except ValueError:
        return None
    if delta < 0 or delta >= (1 << 24):
        return None
    return delta.to_bytes(3, "big")


def _double_esc(chunk: bytes) -> bytes:
    return chunk.replace(bytes([ESC]), bytes([ESC, 0x00]))


def _encode(data: bytes) -> bytes:
    parts: list[bytes] = []
    pos = 0
    for m in ISO_DATE_RE.finditer(data):
        parts.append(_double_esc(data[pos : m.start()]))
        y = int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        encoded = _encode_date(y, mo, d)
        if encoded is None:
            parts.append(_double_esc(m.group(0)))
        else:
            parts.append(bytes([ESC, DATE_TAG]) + encoded)
        pos = m.end()
    parts.append(_double_esc(data[pos:]))
    return b"".join(parts)


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
            raise ValueError("trailing ESC with no marker")
        tag = stream[pos]
        pos += 1
        if tag == 0x00:
            out.append(bytes([ESC]))
        elif tag == DATE_TAG:
            days = int.from_bytes(stream[pos : pos + 3], "big")
            pos += 3
            date = EPOCH + _dt.timedelta(days=days)
            out.append(
                f"{date.year:04d}-{date.month:02d}-{date.day:02d}".encode("ascii")
            )
        else:
            raise ValueError(f"bad marker {tag:#x} at offset {pos - 1}")
    return b"".join(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode(data))


def decompress(data: bytes) -> bytes:
    return _decode(_cmix("-d", data))
