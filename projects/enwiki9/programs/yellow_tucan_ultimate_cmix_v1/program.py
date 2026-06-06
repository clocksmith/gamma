"""yellow_tucan_ultimate_cmix_v1.

Single-pass reversible feature grammar followed by cmix. It combines:
  * MediaWiki/XML opcode tokens,
  * online wiki-link table references,
  * ISO-date/year/integer semantic codes.

The encoder uses one escape grammar over the original byte stream, so regex
passes never scan another layer's binary payload. This is the strongest
byte-rewrite architecture test before a modified-cmix zero-archive sidecar.

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

ESC = 0x00
TAG_LITERAL_ESC = 0x00
TAG_TITLE_NEW = 0x40
TAG_TITLE_REF = 0x41
TAG_TITLE_REF_ALT = 0x42
TAG_DATE = 0x43
TAG_YEAR = 0x44
TAG_UINT = 0x45
EPOCH = _dt.date(1500, 1, 1)

TOKENS = [
    b'<text xml:space="preserve">',
    b"</text>",
    b"<page>",
    b"</page>",
    b"<revision>",
    b"</revision>",
    b"<contributor>",
    b"</contributor>",
    b"<timestamp>",
    b"</timestamp>",
    b"<username>",
    b"</username>",
    b"<comment>",
    b"</comment>",
    b"<title>",
    b"</title>",
    b"<id>",
    b"</id>",
    b"<minor />",
    b"{{",
    b"}}",
    b"[[Category:",
    b"[[Image:",
    b"[[",
    b"]]",
    b"&quot;",
    b"&lt;",
    b"&gt;",
    b"&amp;",
    b"http://",
    b"https://",
    b"<ref",
    b"</ref>",
    b"|thumb",
    b"|right",
    b"|left",
    b"Category:",
    b"File:",
    b"Image:",
]

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
TOKEN_DECODE = {i: token for i, token in enumerate(TOKENS, 1)}
LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")
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


def _date_payload(raw: bytes) -> bytes | None:
    y = int(raw[0:4])
    m = int(raw[5:7])
    d = int(raw[8:10])
    try:
        delta = (_dt.date(y, m, d) - EPOCH).days
    except ValueError:
        return None
    return delta.to_bytes(3, "big") if 0 <= delta < (1 << 24) else None


def _emit_numeric(raw: bytes, match: re.Match[bytes]) -> bytes | None:
    if match.group("date") is not None:
        payload = _date_payload(raw)
        return bytes([ESC, TAG_DATE]) + payload if payload is not None else None
    if match.group("year") is not None:
        return bytes([ESC, TAG_YEAR]) + (int(raw) - 1500).to_bytes(2, "big")
    payload = _varint(int(raw))
    encoded = bytes([ESC, TAG_UINT]) + payload
    return encoded if len(encoded) < len(raw) else None


def _encode(data: bytes) -> bytes:
    out = bytearray()
    vocab: dict[bytes, int] = {}
    i = 0
    token_count = syntax_bytes = 0
    link_new = link_ref = link_alt = link_bytes = 0
    date_count = year_count = uint_count = numeric_bytes = 0
    n = len(data)
    while i < n:
        if data[i] == ESC:
            out.extend((ESC, TAG_LITERAL_ESC))
            i += 1
            continue

        link = LINK_RE.match(data, i)
        if link is not None:
            title = link.group(1)
            alt = link.group(3)
            idx = vocab.get(title)
            link_bytes += link.end() - link.start()
            if idx is None:
                vocab[title] = len(vocab)
                link_new += 1
                out.extend((ESC, TAG_TITLE_NEW))
                out.extend(_varint(len(title)))
                out.extend(title)
                if alt is None:
                    out.append(0)
                else:
                    link_alt += 1
                    out.append(1)
                    out.extend(_varint(len(alt)))
                    out.extend(alt)
            elif alt is None:
                link_ref += 1
                out.extend((ESC, TAG_TITLE_REF))
                out.extend(_varint(idx))
            else:
                link_ref += 1
                link_alt += 1
                out.extend((ESC, TAG_TITLE_REF_ALT))
                out.extend(_varint(idx))
                out.extend(_varint(len(alt)))
                out.extend(alt)
            i = link.end()
            continue

        num = NUM_RE.match(data, i)
        if num is not None:
            raw = num.group(0)
            encoded = _emit_numeric(raw, num)
            if encoded is not None:
                out.extend(encoded)
                numeric_bytes += len(raw)
                if num.group("date") is not None:
                    date_count += 1
                elif num.group("year") is not None:
                    year_count += 1
                else:
                    uint_count += 1
                i = num.end()
                continue

        for code, token in TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((ESC, code))
                i += len(token)
                token_count += 1
                syntax_bytes += len(token)
                break
        else:
            out.append(data[i])
            i += 1

    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "transformed_size": len(out),
            "opcode_token_count": token_count,
            "syntax_matched_bytes": syntax_bytes,
            "syntax_deleted_bytes": max(0, syntax_bytes - 2 * token_count),
            "link_source_bytes": link_bytes,
            "link_vocab_size": len(vocab),
            "link_new_count": link_new,
            "link_ref_count": link_ref,
            "link_alt_count": link_alt,
            "numeric_source_bytes": numeric_bytes,
            "date_count": date_count,
            "year_count": year_count,
            "uint_count": uint_count,
        }
    )
    return bytes(out)


def _decode(stream: bytes) -> bytes:
    out = bytearray()
    vocab: list[bytes] = []
    i = 0
    n = len(stream)
    while i < n:
        b = stream[i]
        if b != ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated escape")
        tag = stream[i + 1]
        i += 2
        if tag == TAG_LITERAL_ESC:
            out.append(ESC)
        elif 1 <= tag <= len(TOKENS):
            out.extend(TOKEN_DECODE[tag])
        elif tag == TAG_TITLE_NEW:
            ln, i = _read_varint(stream, i)
            title = stream[i : i + ln]
            if len(title) != ln:
                raise ValueError("truncated title")
            i += ln
            vocab.append(title)
            if i >= n:
                raise ValueError("truncated title alt flag")
            flag = stream[i]
            i += 1
            if flag == 0:
                out.extend(b"[[" + title + b"]]")
            elif flag == 1:
                ln2, i = _read_varint(stream, i)
                alt = stream[i : i + ln2]
                if len(alt) != ln2:
                    raise ValueError("truncated alt")
                i += ln2
                out.extend(b"[[" + title + b"|" + alt + b"]]")
            else:
                raise ValueError(f"bad title alt flag {flag:#x}")
        elif tag == TAG_TITLE_REF:
            idx, i = _read_varint(stream, i)
            out.extend(b"[[" + vocab[idx] + b"]]")
        elif tag == TAG_TITLE_REF_ALT:
            idx, i = _read_varint(stream, i)
            ln2, i = _read_varint(stream, i)
            alt = stream[i : i + ln2]
            if len(alt) != ln2:
                raise ValueError("truncated ref alt")
            i += ln2
            out.extend(b"[[" + vocab[idx] + b"|" + alt + b"]]")
        elif tag == TAG_DATE:
            payload = stream[i : i + 3]
            if len(payload) != 3:
                raise ValueError("truncated date")
            i += 3
            date = EPOCH + _dt.timedelta(days=int.from_bytes(payload, "big"))
            out.extend(f"{date.year:04d}-{date.month:02d}-{date.day:02d}".encode())
        elif tag == TAG_YEAR:
            payload = stream[i : i + 2]
            if len(payload) != 2:
                raise ValueError("truncated year")
            i += 2
            out.extend(str(1500 + int.from_bytes(payload, "big")).encode())
        elif tag == TAG_UINT:
            value, i = _read_varint(stream, i)
            out.extend(str(value).encode())
        else:
            raise ValueError(f"bad tag {tag:#x}")
    return bytes(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode(data))


def decompress(data: bytes) -> bytes:
    return _decode(_cmix("-d", data))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
