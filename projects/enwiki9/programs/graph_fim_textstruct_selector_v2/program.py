from __future__ import annotations

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
MARK = 0
TOKENS = sorted(
    b"""<text xml:space="preserve">
</text>
<page>
</page>
<revision>
</revision>
<contributor>
</contributor>
<timestamp>
</timestamp>
<username>
</username>
<comment>
</comment>
<title>
</title>
<id>
</id>
<minor />
{{
}}
[[Category:
[[Image:
[[
]]
&quot;
&lt;
&gt;
&amp;
http://
https://
<ref
</ref>
|thumb
|right
|left
Category:
File:
Image:
|url=
|title=
|date=
|accessdate=
|publisher=
|author=
|first=
|last=""".splitlines(),
    key=len,
    reverse=True,
)


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


def _emit_marked(out: bytearray, chunk: bytes) -> None:
    if MARK not in chunk:
        out.extend(chunk)
        return
    for b in chunk:
        if b == MARK:
            out.extend((MARK, 0))
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
        _emit_marked(skel, data[pos : m.end()])
        skel.extend((MARK, code))
        channels[code].append(data[m.end() : end])
        pos = end
    _emit_marked(skel, data[pos:])
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
            out.append(MARK)
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


def _unpack_list(data: bytes, pos: int) -> tuple[list[bytes], int]:
    n, pos = _getv(data, pos)
    out = []
    for _ in range(n):
        size, pos = _getv(data, pos)
        out.append(data[pos : pos + size])
        pos += size
    return out, pos


def _scan_template(data: bytes, i: int) -> int:
    if not data.startswith(b"{{", i):
        return 0
    depth = 1
    j = i + 2
    n = len(data)
    while j + 1 < n:
        if data[j] == 123 and data[j + 1] == 123:
            depth += 1
            j += 2
        elif data[j] == 125 and data[j + 1] == 125:
            depth -= 1
            j += 2
            if depth == 0:
                return j - i
        else:
            j += 1
    return 0


def _scan_ref(data: bytes, i: int) -> int:
    if not (data.startswith(b"<ref", i) or data.startswith(b"<REF", i)):
        return 0
    gt = data.find(b">", i + 4)
    if gt < 0:
        return 0
    if gt > i and data[gt - 1] == 47:
        return gt + 1 - i
    end = data.find(b"</ref>", gt + 1)
    if end < 0:
        end = data.find(b"</REF>", gt + 1)
    if end < 0:
        return 0
    return end + 6 - i


def _scan_link(data: bytes, i: int) -> int:
    if not data.startswith(b"[[", i):
        return 0
    end = data.find(b"]]", i + 2)
    if end < 0:
        return 0
    return end + 2 - i


def _split_top_level(inner: bytes, sep: int) -> list[bytes] | None:
    parts = []
    cur = bytearray()
    tdepth = 0
    ldepth = 0
    i = 0
    while i < len(inner):
        if i + 1 < len(inner):
            pair = inner[i : i + 2]
            if pair == b"{{":
                tdepth += 1
                cur.extend(pair)
                i += 2
                continue
            if pair == b"}}":
                if tdepth == 0:
                    return None
                tdepth -= 1
                cur.extend(pair)
                i += 2
                continue
            if pair == b"[[":
                ldepth += 1
                cur.extend(pair)
                i += 2
                continue
            if pair == b"]]":
                if ldepth == 0:
                    return None
                ldepth -= 1
                cur.extend(pair)
                i += 2
                continue
        if inner[i] == sep and tdepth == 0 and ldepth == 0:
            parts.append(bytes(cur))
            cur.clear()
            i += 1
            continue
        cur.append(inner[i])
        i += 1
    if tdepth or ldepth:
        return None
    parts.append(bytes(cur))
    return parts


def _find_top_level(raw: bytes, target: int) -> int | None:
    tdepth = 0
    ldepth = 0
    i = 0
    while i < len(raw):
        if i + 1 < len(raw):
            pair = raw[i : i + 2]
            if pair == b"{{":
                tdepth += 1
                i += 2
                continue
            if pair == b"}}":
                if tdepth:
                    tdepth -= 1
                i += 2
                continue
            if pair == b"[[":
                ldepth += 1
                i += 2
                continue
            if pair == b"]]":
                if ldepth:
                    ldepth -= 1
                i += 2
                continue
        if raw[i] == target and tdepth == 0 and ldepth == 0:
            return i
        i += 1
    return None


def _parse_template(raw: bytes):
    inner = raw[2:-2]
    parts = _split_top_level(inner, ord("|"))
    if not parts or not parts[0]:
        return None
    args = []
    for arg in parts[1:]:
        eq = _find_top_level(arg, ord("="))
        if eq is None:
            args.append((None, arg))
        else:
            args.append((arg[:eq], arg[eq + 1 :]))
    return parts[0], args


def _template_bytes(record) -> bytes:
    name, args = record
    out = bytearray(b"{{")
    out.extend(name)
    for key, val in args:
        out.append(124)
        if key is not None:
            out.extend(key)
            out.append(61)
        out.extend(val)
    out.extend(b"}}")
    return bytes(out)


def _pack_templates(records: list) -> bytes:
    out = bytearray()
    _putv(out, len(records))
    for name, args in records:
        _putv(out, len(name))
        out.extend(name)
        _putv(out, len(args))
        for key, val in args:
            if key is None:
                out.append(0)
            else:
                out.append(1)
                _putv(out, len(key))
                out.extend(key)
            _putv(out, len(val))
            out.extend(val)
    return bytes(out)


def _unpack_templates(data: bytes, pos: int) -> tuple[list, int]:
    n, pos = _getv(data, pos)
    records = []
    for _ in range(n):
        size, pos = _getv(data, pos)
        name = data[pos : pos + size]
        pos += size
        argc, pos = _getv(data, pos)
        args = []
        for _ in range(argc):
            tag = data[pos]
            pos += 1
            if tag:
                klen, pos = _getv(data, pos)
                key = data[pos : pos + klen]
                pos += klen
            else:
                key = None
            vlen, pos = _getv(data, pos)
            val = data[pos : pos + vlen]
            pos += vlen
            args.append((key, val))
        records.append((name, args))
    return records, pos


def _extract_text(text: bytes) -> tuple[bytes, list]:
    out = bytearray()
    templates: list = []
    i = 0
    n = len(text)
    while i < n:
        length = _scan_template(text, i)
        if length:
            raw = text[i : i + length]
            record = _parse_template(raw)
            if record is not None and _template_bytes(record) == raw:
                out.extend((MARK, 1))
                templates.append(record)
                i += length
                continue
        b = text[i]
        if b == MARK:
            out.extend((MARK, 0))
        else:
            out.append(b)
        i += 1
    return bytes(out), templates


def _restore_text(skel: bytes, templates: list) -> bytes:
    idx_t = 0
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
            out.append(MARK)
        elif code == 1:
            out.extend(_template_bytes(templates[idx_t]))
            idx_t += 1
        else:
            raise ValueError("bad text marker")
    return bytes(out)


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


def _pack_tokens(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == MARK:
            out.extend((MARK, 255))
            i += 1
            continue
        for code, token in enumerate(TOKENS, 1):
            if data.startswith(token, i):
                out.extend((MARK, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _unpack_tokens(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b:
            out.append(b)
            i += 1
            continue
        code = data[i + 1]
        i += 2
        if code == 255:
            out.append(MARK)
        elif 1 <= code <= len(TOKENS):
            out.extend(TOKENS[code - 1])
        else:
            raise ValueError("bad token code")
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


def _pack_graph_textstruct(data: bytes) -> bytes:
    skel, channels = _split(data)
    text_skeletons = []
    templates: list = []
    for text in channels[6]:
        ts, tt = _extract_text(text)
        text_skeletons.append(ts)
        templates.extend(tt)
    out = bytearray(b"GS2")
    _putv(out, len(skel))
    out.extend(skel)
    for code in range(1, 6):
        out.extend(_pack_list(channels[code]))
    out.extend(_pack_list(text_skeletons))
    out.extend(_pack_templates(templates))
    return bytes(out)


def _unpack_graph_textstruct(data: bytes) -> bytes:
    if data[:3] != b"GS2":
        raise ValueError("bad graph textstruct pack")
    pos = 3
    skel_len, pos = _getv(data, pos)
    skel = data[pos : pos + skel_len]
    pos += skel_len
    channels: list[list[bytes]] = [[] for _ in range(7)]
    for code in range(1, 6):
        channels[code], pos = _unpack_list(data, pos)
    text_skeletons, pos = _unpack_list(data, pos)
    templates, pos = _unpack_templates(data, pos)
    channels[6] = []
    ti = 0
    for ts in text_skeletons:
        need_t = ts.count(bytes((MARK, 1)))
        channels[6].append(_restore_text(ts, templates[ti : ti + need_t]))
        ti += need_t
    return _join(skel, channels)


def compress(data: bytes) -> bytes:
    raw = b"R" + _xz(data)
    graph_v1 = _pack_graph_v1(data)
    graph = b"F" + _xz(_pack_words(graph_v1))
    opcode_graph = b"O" + _xz(_pack_words(_pack_tokens(graph_v1)))
    textstruct = b"S" + _xz(_pack_words(_pack_graph_textstruct(data)))
    return min((raw, graph, opcode_graph, textstruct), key=len)


def decompress(data: bytes) -> bytes:
    mode = data[:1]
    payload = data[1:]
    if mode == b"R":
        return _unxz(payload)
    if mode == b"F":
        return _unpack_graph_v1(_unpack_words(_unxz(payload)))
    if mode == b"O":
        return _unpack_graph_v1(_unpack_tokens(_unpack_words(_unxz(payload))))
    if mode == b"S":
        return _unpack_graph_textstruct(_unpack_words(_unxz(payload)))
    raise ValueError("bad graph_fim_textstruct mode")
