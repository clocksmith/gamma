from __future__ import annotations

import gzip
import os
import pathlib
import re
import stat
import subprocess
import tempfile

MAGIC = b"FBD1"
MODE_RAW = 0
MODE_BLOCKS = 1
ESC = 1
ESC_LIT = 0
ESC_PROSE_BLOCK = 3
ESC_NUM_BLOCK = 4
PROSE_FIELDS = (
    (b'<text xml:space="preserve">', b"</text>"),
    (b"<title>", b"</title>"),
    (b"<comment>", b"</comment>"),
    (b"<username>", b"</username>"),
    (b"<sitename>", b"</sitename>"),
    (b"<base>", b"</base>"),
)
VALUE_FIELDS = (
    (b"<timestamp>", b"</timestamp>"),
    (b"<id>", b"</id>"),
    (b"<ip>", b"</ip>"),
)
FIELDS = tuple((a, b, ESC_PROSE_BLOCK) for a, b in PROSE_FIELDS) + tuple(
    (a, b, ESC_NUM_BLOCK) for a, b in VALUE_FIELDS
)
FIELDS = tuple(sorted(FIELDS, key=lambda item: len(item[0]), reverse=True))

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_DICT_GZ = _DIR / "english.dic.gz"
_extracted_bin: pathlib.Path | None = None
_extracted_dict: pathlib.Path | None = None
_S: dict = {}


def _uvar(n: int) -> bytes:
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def _ruvar(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        b = buf[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def _extract(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, path = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    p = pathlib.Path(path)
    with gzip.open(src, "rb") as inp:
        p.write_bytes(inp.read())
    if executable:
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def _binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is None or not _extracted_bin.exists():
        _extracted_bin = _extract(_BIN_GZ, "fx2-block-demux-cmix-", True)
    return _extracted_bin


def _dictionary() -> pathlib.Path:
    global _extracted_dict
    if _extracted_dict is None or not _extracted_dict.exists():
        _extracted_dict = _extract(_DICT_GZ, "fx2-block-demux-dict-", False)
    return _extracted_dict


def _fx2(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(_binary()), flag, str(_dictionary()), src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def _put_skel(out: bytearray, b: int) -> None:
    if b == ESC:
        out.extend((ESC, ESC_LIT))
    else:
        out.append(b)


def _split_blocks(data: bytes) -> tuple[bytes, bytes, bytes]:
    skel = bytearray()
    prose = bytearray()
    nums = bytearray()
    i = 0
    n = len(data)
    while i < n:
        matched = False
        for open_tag, close_tag, tag in FIELDS:
            if not data.startswith(open_tag, i):
                continue
            start = i + len(open_tag)
            end = data.find(close_tag, start)
            if end < 0:
                break
            for c in open_tag:
                _put_skel(skel, c)
            body = data[start:end]
            if tag == ESC_PROSE_BLOCK:
                prose.extend(body)
            else:
                nums.extend(body)
            skel.extend((ESC, tag))
            skel.extend(_uvar(len(body)))
            for c in close_tag:
                _put_skel(skel, c)
            i = end + len(close_tag)
            matched = True
            break
        if matched:
            continue
        _put_skel(skel, data[i])
        i += 1
    return bytes(skel), bytes(prose), bytes(nums)


def _join_blocks(skel: bytes, prose: bytes, nums: bytes) -> bytes:
    out = bytearray()
    pp = 0
    np = 0
    i = 0
    n = len(skel)
    while i < n:
        b = skel[i]
        i += 1
        if b != ESC:
            out.append(b)
            continue
        if i >= n:
            raise ValueError("trailing escape")
        tag = skel[i]
        i += 1
        if tag == ESC_LIT:
            out.append(ESC)
        elif tag == ESC_PROSE_BLOCK:
            size, i = _ruvar(skel, i)
            out.extend(prose[pp:pp + size])
            pp += size
        elif tag == ESC_NUM_BLOCK:
            size, i = _ruvar(skel, i)
            out.extend(nums[np:np + size])
            np += size
        else:
            raise ValueError("bad block escape tag")
    if pp != len(prose) or np != len(nums):
        raise ValueError("unused block bytes")
    return bytes(out)


def _pack_blocks(data: bytes) -> tuple[bytes, dict]:
    skel, prose, nums = _split_blocks(data)
    cskel = _fx2("-c", skel)
    cprose = _fx2("-c", prose)
    cnums = _fx2("-c", nums)
    body = bytearray(MAGIC)
    body.append(MODE_BLOCKS)
    for part in (cskel, cprose, cnums):
        body.extend(_uvar(len(part)))
    body.extend(cskel)
    body.extend(cprose)
    body.extend(cnums)
    return bytes(body), {
        "mode": "block_demux",
        "raw_streams": {
            "syntax_skeleton": len(skel),
            "prose_blocks": len(prose),
            "numeric_values": len(nums),
        },
        "compressed_streams": {
            "syntax_skeleton": len(cskel),
            "prose_blocks": len(cprose),
            "numeric_values": len(cnums),
        },
    }


def compress(data: bytes) -> bytes:
    raw_body = _fx2("-c", data)
    raw = MAGIC + bytes([MODE_RAW]) + raw_body
    block, info = _pack_blocks(data)
    chosen = block if len(block) < len(raw) else raw
    _S.clear()
    _S.update({
        "selected_mode": "block_demux" if chosen is block else "raw_fx2",
        "candidate_archives": {
            "raw_fx2": len(raw),
            "block_demux": len(block),
        },
        "block_demux": info,
    })
    return chosen


def decompress(data: bytes) -> bytes:
    if not data.startswith(MAGIC):
        raise ValueError("bad magic")
    pos = len(MAGIC)
    mode = data[pos]
    pos += 1
    if mode == MODE_RAW:
        return _fx2("-d", data[pos:])
    if mode != MODE_BLOCKS:
        raise ValueError("bad mode")
    sizes = []
    for _ in range(3):
        size, pos = _ruvar(data, pos)
        sizes.append(size)
    cskel = data[pos:pos + sizes[0]]
    pos += sizes[0]
    cprose = data[pos:pos + sizes[1]]
    pos += sizes[1]
    cnums = data[pos:pos + sizes[2]]
    skel = _fx2("-d", cskel)
    prose = _fx2("-d", cprose)
    nums = _fx2("-d", cnums)
    return _join_blocks(skel, prose, nums)


def stats() -> dict:
    return dict(_S)
