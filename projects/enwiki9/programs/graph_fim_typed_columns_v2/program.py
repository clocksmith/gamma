from __future__ import annotations

from datetime import datetime, timezone
import re
import subprocess

XZ = ["xz", "-q", "-c", "-T1", "--check=crc32", "--lzma2=preset=9e,dict=1024MiB"]
UNXZ = ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"]
OPEN_RE = re.compile(
    rb"<title>|<id>|<timestamp>|<username>|<comment>|<text xml:space=\"preserve\">"
)
FIELDS = {
    b"<title>": (1, b"</title>"),
    b"<id>": (2, b"</id>"),
    b"<timestamp>": (3, b"</timestamp>"),
    b"<username>": (4, b"</username>"),
    b"<comment>": (5, b"</comment>"),
    b'<text xml:space="preserve">': (6, b"</text>"),
}
WORD_RE = re.compile(rb"[A-Za-z]{3,32}")
ESC = 2
BASE = 128
MAX_WORDS = 128


def _xz(data: bytes) -> bytes:
    return subprocess.run(XZ, input=data, stdout=subprocess.PIPE, check=True).stdout


def _unxz(data: bytes) -> bytes:
    return subprocess.run(UNXZ, input=data, stdout=subprocess.PIPE, check=True).stdout


def _putv(out: bytearray, n: int) -> None:
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)


def _getv(data: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def _zz(n: int) -> int:
    return n << 1 if n >= 0 else ((-n) << 1) - 1


def _unz(n: int) -> int:
    return n >> 1 if n & 1 == 0 else -((n + 1) >> 1)


def _emit_skel(out: bytearray, chunk: bytes) -> None:
    if 0 not in chunk:
        out.extend(chunk)
        return
    for b in chunk:
        if b == 0:
            out.extend((0, 0))
        else:
            out.append(b)


def _split(data: bytes) -> tuple[bytes, list[list[bytes]]]:
    skel = bytearray()
    channels: list[list[bytes]] = [[] for _ in range(7)]
    pos = 0
    for m in OPEN_RE.finditer(data):
        if m.start() < pos:
            continue
        code, close = FIELDS[m.group(0)]
        end = data.find(close, m.end())
        if end < 0:
            continue
        _emit_skel(skel, data[pos : m.end()])
        skel.extend((0, code))
        channels[code].append(data[m.end() : end])
        pos = end
    _emit_skel(skel, data[pos:])
    return bytes(skel), channels


def _join(skel: bytes, channels: list[list[bytes]]) -> bytes:
    idx = [0] * 7
    out = bytearray()
    i = 0
    while i < len(skel):
        b = skel[i]
        if b:
            out.append(b)
            i += 1
            continue
        code = skel[i + 1]
        i += 2
        if code == 0:
            out.append(0)
        else:
            j = idx[code]
            out.extend(channels[code][j])
            idx[code] = j + 1
    return bytes(out)


def _pack_list(items: list[bytes]) -> bytes:
    out = bytearray()
    _putv(out, len(items))
    for item in items:
        _putv(out, len(item))
        out.extend(item)
    return bytes(out)


def _unpack_list(data: bytes, pos: int = 0) -> tuple[list[bytes], int]:
    n, pos = _getv(data, pos)
    out = []
    for _ in range(n):
        size, pos = _getv(data, pos)
        out.append(data[pos : pos + size])
        pos += size
    return out, pos


def _lcp(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b), 255)
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _pack_front(items: list[bytes]) -> bytes:
    out = bytearray()
    _putv(out, len(items))
    prev = b""
    for item in items:
        p = _lcp(prev, item)
        suffix = item[p:]
        _putv(out, p)
        _putv(out, len(suffix))
        out.extend(suffix)
        prev = item
    return bytes(out)


def _unpack_front(data: bytes, pos: int = 0) -> tuple[list[bytes], int]:
    n, pos = _getv(data, pos)
    prev = b""
    out = []
    for _ in range(n):
        p, pos = _getv(data, pos)
        size, pos = _getv(data, pos)
        item = prev[:p] + data[pos : pos + size]
        pos += size
        out.append(item)
        prev = item
    return out, pos


def _pack_ints(items: list[bytes]) -> bytes:
    out = bytearray()
    _putv(out, len(items))
    prev = 0
    for item in items:
        if item.isdigit() and (item == b"0" or not item.startswith(b"0")):
            n = int(item)
            out.append(1)
            _putv(out, _zz(n - prev))
            prev = n
        else:
            out.append(0)
            _putv(out, len(item))
            out.extend(item)
    return bytes(out)


def _unpack_ints(data: bytes, pos: int = 0) -> tuple[list[bytes], int]:
    n, pos = _getv(data, pos)
    prev = 0
    out = []
    for _ in range(n):
        tag = data[pos]
        pos += 1
        if tag:
            delta, pos = _getv(data, pos)
            prev += _unz(delta)
            out.append(str(prev).encode())
        else:
            size, pos = _getv(data, pos)
            out.append(data[pos : pos + size])
            pos += size
    return out, pos


def _parse_ts(item: bytes) -> int | None:
    try:
        if len(item) != 20 or item[4] != 45 or item[7] != 45 or item[10] != 84 or item[13] != 58 or item[16] != 58 or item[19] != 90:
            return None
        dt = datetime(
            int(item[0:4]), int(item[5:7]), int(item[8:10]),
            int(item[11:13]), int(item[14:16]), int(item[17:19]),
            tzinfo=timezone.utc,
        )
        return int(dt.timestamp())
    except ValueError:
        return None


def _format_ts(n: int) -> bytes:
    dt = datetime.fromtimestamp(n, timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}Z".encode()


def _pack_times(items: list[bytes]) -> bytes:
    out = bytearray()
    _putv(out, len(items))
    prev = 0
    for item in items:
        n = _parse_ts(item)
        if n is None:
            out.append(0)
            _putv(out, len(item))
            out.extend(item)
        else:
            out.append(1)
            _putv(out, _zz(n - prev))
            prev = n
    return bytes(out)


def _unpack_times(data: bytes, pos: int = 0) -> tuple[list[bytes], int]:
    n, pos = _getv(data, pos)
    prev = 0
    out = []
    for _ in range(n):
        tag = data[pos]
        pos += 1
        if tag:
            delta, pos = _getv(data, pos)
            prev += _unz(delta)
            out.append(_format_ts(prev))
        else:
            size, pos = _getv(data, pos)
            out.append(data[pos : pos + size])
            pos += size
    return out, pos


def _pick_words(data: bytes) -> list[bytes]:
    counts: dict[bytes, int] = {}
    for m in WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    scored = []
    for w, f in counts.items():
        save = f * (len(w) - 1) - len(w) - 1
        if save > 0:
            scored.append((save, w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:MAX_WORDS]]


def _esc(data: bytes) -> bytes:
    if not any(b == ESC or b >= BASE for b in data):
        return data
    out = bytearray()
    for b in data:
        if b == ESC or b >= BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _pack_words(data: bytes) -> bytes:
    words = _pick_words(data)
    out = bytearray(b"WD1")
    _putv(out, len(words))
    for w in words:
        _putv(out, len(w))
        out.extend(w)
    if not words:
        out.extend(_esc(data))
        return bytes(out)
    code = {w: bytes([BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    pos = 0
    for m in pat.finditer(data):
        out.extend(_esc(data[pos : m.start()]))
        out.extend(code[m.group(0)])
        pos = m.end()
    out.extend(_esc(data[pos:]))
    return bytes(out)


def _unpack_words(data: bytes) -> bytes:
    if data[:3] != b"WD1":
        raise ValueError("bad word pack")
    pos = 3
    n, pos = _getv(data, pos)
    words = []
    for _ in range(n):
        size, pos = _getv(data, pos)
        words.append(data[pos : pos + size])
        pos += size
    out = bytearray()
    while pos < len(data):
        b = data[pos]
        pos += 1
        if b == ESC:
            out.append(data[pos])
            pos += 1
        elif b >= BASE:
            out.extend(words[b - BASE])
        else:
            out.append(b)
    return bytes(out)


def _pack_graph_v1(data: bytes) -> bytes:
    skel, channels = _split(data)
    out = bytearray(b"GF1")
    _putv(out, len(skel))
    out.extend(skel)
    for code in range(1, 7):
        out.extend(_pack_list(channels[code]))
    return bytes(out)


def _unpack_graph_v1(data: bytes) -> bytes:
    if data[:3] != b"GF1":
        raise ValueError("bad graph v1 pack")
    pos = 3
    skel_len, pos = _getv(data, pos)
    skel = data[pos : pos + skel_len]
    pos += skel_len
    channels: list[list[bytes]] = [[] for _ in range(7)]
    for code in range(1, 7):
        channels[code], pos = _unpack_list(data, pos)
    return _join(skel, channels)


def _pack_graph_typed(data: bytes) -> bytes:
    skel, channels = _split(data)
    out = bytearray(b"GT2")
    _putv(out, len(skel))
    out.extend(skel)
    blocks = {
        1: (b"F", _pack_front(channels[1])),
        2: (b"I", _pack_ints(channels[2])),
        3: (b"T", _pack_times(channels[3])),
        4: (b"F", _pack_front(channels[4])),
        5: (b"F", _pack_front(channels[5])),
        6: (b"L", _pack_list(channels[6])),
    }
    for code in range(1, 7):
        tag, payload = blocks[code]
        out.extend(tag)
        _putv(out, len(payload))
        out.extend(payload)
    return bytes(out)


def _unpack_graph_typed(data: bytes) -> bytes:
    if data[:3] != b"GT2":
        raise ValueError("bad graph typed pack")
    pos = 3
    skel_len, pos = _getv(data, pos)
    skel = data[pos : pos + skel_len]
    pos += skel_len
    channels: list[list[bytes]] = [[] for _ in range(7)]
    for code in range(1, 7):
        tag = data[pos : pos + 1]
        pos += 1
        size, pos = _getv(data, pos)
        block = data[pos : pos + size]
        pos += size
        if tag == b"L":
            channels[code], _ = _unpack_list(block)
        elif tag == b"F":
            channels[code], _ = _unpack_front(block)
        elif tag == b"I" and code == 2:
            channels[code], _ = _unpack_ints(block)
        elif tag == b"T" and code == 3:
            channels[code], _ = _unpack_times(block)
        else:
            raise ValueError("bad typed channel")
    return _join(skel, channels)


def compress(data: bytes) -> bytes:
    raw = b"R" + _xz(data)
    graph = b"F" + _xz(_pack_words(_pack_graph_v1(data)))
    typed = b"T" + _xz(_pack_graph_typed(data))
    typed_words = b"W" + _xz(_pack_words(_pack_graph_typed(data)))
    return min((raw, graph, typed, typed_words), key=len)


def decompress(data: bytes) -> bytes:
    mode = data[:1]
    payload = data[1:]
    if mode == b"R":
        return _unxz(payload)
    if mode == b"F":
        return _unpack_graph_v1(_unpack_words(_unxz(payload)))
    if mode == b"T":
        return _unpack_graph_typed(_unxz(payload))
    if mode == b"W":
        return _unpack_graph_typed(_unpack_words(_unxz(payload)))
    raise ValueError("bad graph_fim_typed_columns mode")
