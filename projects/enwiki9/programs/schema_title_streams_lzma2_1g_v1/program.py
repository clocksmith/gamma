from __future__ import annotations

import hashlib
import lzma
import re
import struct

PRESET = 9 | lzma.PRESET_EXTREME
FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": PRESET, "dict_size": 1 << 30}]
MAGIC = b"STL1"
MODE_LITERAL = 0
MODE_TYPED = 1
MODE_TOPIC = 2

TEXT_OPEN = b'<text xml:space="preserve">'
TEXT_CLOSE = b"</text>"
TEXT_JOIN = b"\x00\x00\xfd\xe0"
SENT = {
    "text": b"\x00\x00\xfd\xe1",
    "title": b"\x00\x00\xfd\xe2",
    "id": b"\x00\x00\xfd\xe3",
    "timestamp": b"\x00\x00\xfd\xe4",
    "username": b"\x00\x00\xfd\xe5",
    "ip": b"\x00\x00\xfd\xe6",
    "comment": b"\x00\x00\xfd\xe7",
}
FIELDS = ["title", "id", "timestamp", "username", "ip", "comment"]
CHANNELS = ["literal", "scaffold", "text", "atoms"]
CHANNEL_ID = {name: i for i, name in enumerate(CHANNELS)}
CHANNEL_NAME = {i: name for name, i in CHANNEL_ID.items()}

RE_TEXT = re.compile(rb'(<text xml:space="preserve">)(.*?)(</text>)', re.DOTALL)
FIELD_REGEX = [
    ("comment", re.compile(rb"(<comment>)(.*?)(</comment>)", re.DOTALL)),
    ("title", re.compile(rb"(<title>)([^<]*)(</title>)")),
    ("timestamp", re.compile(rb"(<timestamp>)([^<]*)(</timestamp>)")),
    ("username", re.compile(rb"(<username>)([^<]*)(</username>)")),
    ("ip", re.compile(rb"(<ip>)([^<]*)(</ip>)")),
    ("id", re.compile(rb"(<id>)([^<]*)(</id>)")),
]

OP_ESC = 1
OP_LIT_ESC = 255
OP_TOKENS = [
    TEXT_OPEN,
    TEXT_CLOSE,
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
    b"<redirect title=",
]
OP_BY_LEN = sorted(enumerate(OP_TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
OP_DECODE = {i: t for i, t in enumerate(OP_TOKENS, 1)}

TT_ESC = 0x10
TT_LIT_ESC = 0
TT_NEW = 1
TT_REF = 2
TT_REF_ALT = 3
LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")

WC_ESC = 0x02
WC_T2 = 0x03
WC_BASE = 0x80
WC_K1 = 128
WC_K2 = 256
WC_WORD_RE = re.compile(rb"[A-Za-z]{3,32}|\[\[|\]\]|\{\{|\}\}|={2,6}|'{2,5}|&[A-Za-z]+;")

PAGE_RE = re.compile(rb"<page>.*?</page>", re.DOTALL)
PAGE_ID_RE = re.compile(rb"<page>.*?<id>(\d+)</id>", re.DOTALL)
TITLE_RE = re.compile(rb"<title>([^<]*)</title>")
REDIRECT_RE = re.compile(rb"#REDIRECT\s*\[\[([^\]\|]+)", re.IGNORECASE)
CAT_RE = re.compile(rb"\[\[Category:([^\]\|]+)", re.IGNORECASE)
TPL_RE = re.compile(rb"\{\{([A-Za-z0-9 _:-]{2,80})")

_S: dict = {}


def _uvar(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _ruvar(buf: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    n = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _lz(data: bytes) -> bytes:
    return lzma.compress(data, format=lzma.FORMAT_XZ, filters=FILTERS)


def _unlz(data: bytes) -> bytes:
    return lzma.decompress(data)


def _has_collision(data: bytes) -> bool:
    return TEXT_JOIN in data or any(s in data for s in SENT.values())


def _op_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] == OP_ESC:
            out.extend((OP_ESC, OP_LIT_ESC))
            i += 1
            continue
        for code, token in OP_BY_LEN:
            if data.startswith(token, i):
                out.extend((OP_ESC, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _op_decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != OP_ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("trailing opcode escape")
        code = data[i + 1]
        if code == OP_LIT_ESC:
            out.append(OP_ESC)
        else:
            out.extend(OP_DECODE[code])
        i += 2
    return bytes(out)


def _tt_var(n: int) -> bytes:
    return _uvar(n)


def _tt_read(buf: bytes, pos: int) -> tuple[int, int]:
    return _ruvar(buf, pos)


def _tt_escape(chunk: bytes) -> bytes:
    return chunk.replace(bytes([TT_ESC]), bytes([TT_ESC, TT_LIT_ESC]))


def _tt_encode(data: bytes) -> bytes:
    out: list[bytes] = []
    vocab: dict[bytes, int] = {}
    pos = 0
    for m in LINK_RE.finditer(data):
        out.append(_tt_escape(data[pos:m.start()]))
        title = m.group(1)
        alt = m.group(3)
        idx = vocab.get(title)
        if idx is None:
            vocab[title] = len(vocab)
            out.append(bytes([TT_ESC, TT_NEW]) + _tt_var(len(title)) + title)
            if alt is None:
                out.append(b"\x00")
            else:
                out.append(b"\x01" + _tt_var(len(alt)) + alt)
        elif alt is None:
            out.append(bytes([TT_ESC, TT_REF]) + _tt_var(idx))
        else:
            out.append(bytes([TT_ESC, TT_REF_ALT]) + _tt_var(idx) + _tt_var(len(alt)) + alt)
        pos = m.end()
    out.append(_tt_escape(data[pos:]))
    return b"".join(out)


def _tt_decode(stream: bytes) -> bytes:
    out: list[bytes] = []
    vocab: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        i = stream.find(bytes([TT_ESC]), pos)
        if i < 0:
            out.append(stream[pos:])
            break
        out.append(stream[pos:i])
        pos = i + 1
        tag = stream[pos]
        pos += 1
        if tag == TT_LIT_ESC:
            out.append(bytes([TT_ESC]))
        elif tag == TT_NEW:
            ln, pos = _tt_read(stream, pos)
            title = stream[pos:pos + ln]
            pos += ln
            vocab.append(title)
            has_alt = stream[pos]
            pos += 1
            if has_alt == 0:
                out.append(b"[[" + title + b"]]")
            elif has_alt == 1:
                ln2, pos = _tt_read(stream, pos)
                alt = stream[pos:pos + ln2]
                pos += ln2
                out.append(b"[[" + title + b"|" + alt + b"]]")
            else:
                raise ValueError("bad title alt tag")
        elif tag == TT_REF:
            idx, pos = _tt_read(stream, pos)
            out.append(b"[[" + vocab[idx] + b"]]")
        elif tag == TT_REF_ALT:
            idx, pos = _tt_read(stream, pos)
            ln2, pos = _tt_read(stream, pos)
            alt = stream[pos:pos + ln2]
            pos += ln2
            out.append(b"[[" + vocab[idx] + b"|" + alt + b"]]")
        else:
            raise ValueError("bad title tag")
    return b"".join(out)


def _wc_pick(data: bytes) -> tuple[list[bytes], list[bytes]]:
    counts: dict[bytes, int] = {}
    for m in WC_WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    rows = []
    for w, f in counts.items():
        cost = len(w) + 1
        save1 = f * (len(w) - 1) - cost
        save2 = f * (len(w) - 2) - cost
        rows.append((save1, save2, w))
    rows.sort(key=lambda x: (-x[0], -len(x[2]), x[2]))
    tier1 = [w for s1, _s2, w in rows if s1 > 0][:WC_K1]
    used = set(tier1)
    rest = [(s2, w) for _s1, s2, w in rows if w not in used and s2 > 0]
    rest.sort(key=lambda x: (-x[0], -len(x[1]), x[1]))
    return tier1, [w for _s2, w in rest[:WC_K2]]


def _wc_escape(chunk: bytes) -> bytes:
    if not any(b == WC_ESC or b == WC_T2 or b >= WC_BASE for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b == WC_ESC or b == WC_T2 or b >= WC_BASE:
            out.append(WC_ESC)
        out.append(b)
    return bytes(out)


def _wc_sub(data: bytes, tier1: list[bytes], tier2: list[bytes]) -> bytes:
    cmap: dict[bytes, bytes] = {}
    for i, w in enumerate(tier1):
        cmap[w] = bytes([WC_BASE + i])
    for i, w in enumerate(tier2):
        cmap[w] = bytes([WC_T2, i])
    if not cmap:
        return _wc_escape(data)
    pat = re.compile(b"|".join(re.escape(w) for w in sorted(cmap, key=lambda x: (-len(x), x))))
    out: list[bytes] = []
    pos = 0
    for m in pat.finditer(data):
        out.append(_wc_escape(data[pos:m.start()]))
        out.append(cmap[m.group(0)])
        pos = m.end()
    out.append(_wc_escape(data[pos:]))
    return b"".join(out)


def _wc_pack(data: bytes) -> bytes:
    tier1, tier2 = _wc_pick(data)
    head = bytearray()
    head.extend(_uvar(len(tier1)))
    for w in tier1:
        head.extend(_uvar(len(w)))
        head.extend(w)
    head.extend(_uvar(len(tier2)))
    for w in tier2:
        head.extend(_uvar(len(w)))
        head.extend(w)
    body = _wc_sub(data, tier1, tier2)
    return _uvar(len(head)) + bytes(head) + body


def _wc_expand(body: bytes, tier1: list[bytes], tier2: list[bytes]) -> bytes:
    out = bytearray()
    pos = 0
    n = len(body)
    while pos < n:
        b = body[pos]
        pos += 1
        if b == WC_ESC:
            out.append(body[pos])
            pos += 1
        elif b == WC_T2:
            idx = body[pos]
            pos += 1
            out.extend(tier2[idx])
        elif b >= WC_BASE:
            out.extend(tier1[b - WC_BASE])
        else:
            out.append(b)
    return bytes(out)


def _wc_unpack(data: bytes) -> bytes:
    hlen, pos = _ruvar(data, 0)
    head = data[pos:pos + hlen]
    body = data[pos + hlen:]
    hp = 0
    n1, hp = _ruvar(head, hp)
    tier1 = []
    for _ in range(n1):
        ln, hp = _ruvar(head, hp)
        tier1.append(head[hp:hp + ln])
        hp += ln
    n2, hp = _ruvar(head, hp)
    tier2 = []
    for _ in range(n2):
        ln, hp = _ruvar(head, hp)
        tier2.append(head[hp:hp + ln])
        hp += ln
    return _wc_expand(body, tier1, tier2)


def _pack_text(parts: list[bytes]) -> bytes:
    joined = TEXT_JOIN.join(parts)
    return _uvar(len(parts)) + _wc_pack(_tt_encode(joined))


def _unpack_text(buf: bytes) -> list[bytes]:
    count, pos = _ruvar(buf, 0)
    joined = _tt_decode(_wc_unpack(buf[pos:]))
    if count == 0:
        return []
    parts = joined.split(TEXT_JOIN)
    if len(parts) != count:
        raise ValueError("text part count mismatch")
    return parts


def _front_pack(values: list[bytes]) -> bytes:
    out = bytearray(_uvar(len(values)))
    prev = b""
    for v in values:
        k = 0
        lim = min(len(prev), len(v))
        while k < lim and prev[k] == v[k]:
            k += 1
        suf = v[k:]
        out.extend(_uvar(k))
        out.extend(_uvar(len(suf)))
        out.extend(suf)
        prev = v
    return bytes(out)


def _front_unpack(buf: bytes, pos: int) -> tuple[list[bytes], int]:
    count, pos = _ruvar(buf, pos)
    prev = b""
    out = []
    for _ in range(count):
        pref, pos = _ruvar(buf, pos)
        ln, pos = _ruvar(buf, pos)
        v = prev[:pref] + buf[pos:pos + ln]
        pos += ln
        out.append(v)
        prev = v
    return out, pos


def _pack_atoms(channels: dict[str, list[bytes]]) -> bytes:
    out = bytearray()
    for name in FIELDS:
        out.extend(_front_pack(channels[name]))
    return bytes(out)


def _unpack_atoms(buf: bytes) -> dict[str, list[bytes]]:
    pos = 0
    out = {}
    for name in FIELDS:
        out[name], pos = _front_unpack(buf, pos)
    return out


def _extract(data: bytes) -> tuple[bytes, list[bytes], dict[str, list[bytes]]]:
    text_parts: list[bytes] = []

    def text_repl(m: re.Match) -> bytes:
        text_parts.append(m.group(2))
        return m.group(1) + SENT["text"] + m.group(3)

    scaffold = RE_TEXT.sub(text_repl, data)
    channels: dict[str, list[bytes]] = {name: [] for name in FIELDS}
    for name, rgx in FIELD_REGEX:
        sent = SENT[name]
        vals: list[bytes] = []

        def repl(m: re.Match, _sent=sent, _vals=vals) -> bytes:
            _vals.append(m.group(2))
            return m.group(1) + _sent + m.group(3)

        scaffold = rgx.sub(repl, scaffold)
        channels[name] = vals
    return scaffold, text_parts, channels


def _reassemble(scaffold: bytes, text_parts: list[bytes], channels: dict[str, list[bytes]]) -> bytes:
    values = {"text": iter(text_parts)}
    values.update({name: iter(channels[name]) for name in FIELDS})
    out = bytearray()
    pos = 0
    n = len(scaffold)
    sent_items = sorted(SENT.items(), key=lambda kv: len(kv[1]), reverse=True)
    while pos < n:
        hit = None
        for name, sent in sent_items:
            if scaffold.startswith(sent, pos):
                hit = (name, sent)
                break
        if hit is None:
            out.append(scaffold[pos])
            pos += 1
        else:
            name, sent = hit
            out.extend(next(values[name]))
            pos += len(sent)
    return bytes(out)


def _page_records(data: bytes):
    matches = list(PAGE_RE.finditer(data))
    if not matches:
        return None
    prefix = data[:matches[0].start()]
    records = []
    last = matches[0].start()
    seen = set()
    for m in matches:
        rec = data[last:m.start()] + m.group(0)
        mid = PAGE_ID_RE.search(rec)
        if not mid:
            return None
        pid = int(mid.group(1))
        if pid in seen:
            return None
        seen.add(pid)
        records.append((pid, _topic_key(rec), rec))
        last = m.end()
    return prefix, records, data[last:]


def _topic_key(page: bytes) -> bytes:
    lower = page.lower()
    redir = REDIRECT_RE.search(page)
    if redir:
        return b"~redirect~" + redir.group(1).lower()
    cats = [m.group(1).lower()[:160] for m in CAT_RE.finditer(page)]
    if cats:
        return b"|".join(sorted(cats)[:12])
    tpls = [m.group(1).lower()[:80] for m in TPL_RE.finditer(page)]
    if tpls:
        return b"~tpl~" + b"|".join(sorted(tpls)[:8])
    title = TITLE_RE.search(page)
    if title:
        return b"~title~" + title.group(1).lower()[-80:]
    return lower[:80]


def _topic_reorder(data: bytes) -> bytes | None:
    parsed = _page_records(data)
    if parsed is None:
        return None
    prefix, records, suffix = parsed
    ordered = sorted(records, key=lambda r: (r[1], r[0]))
    return prefix + b"".join(r[2] for r in ordered) + suffix


def _restore_id_order(data: bytes) -> bytes | None:
    parsed = _page_records(data)
    if parsed is None:
        return None
    prefix, records, suffix = parsed
    ordered = sorted(records, key=lambda r: r[0])
    return prefix + b"".join(r[2] for r in ordered) + suffix


def _build(mode: int, bodies: dict[str, bytes], original: bytes) -> bytes:
    packed = []
    for name in CHANNELS:
        if name not in bodies:
            continue
        raw = bodies[name]
        comp = _lz(raw)
        packed.append((CHANNEL_ID[name], len(raw), comp))
    out = bytearray(MAGIC)
    out.append(mode)
    out.extend(struct.pack(">Q", len(original)))
    out.extend(_sha(original))
    out.extend(_uvar(len(packed)))
    for cid, raw_len, comp in packed:
        out.append(cid)
        out.extend(_uvar(raw_len))
        out.extend(_uvar(len(comp)))
    for _cid, _raw_len, comp in packed:
        out.extend(comp)
    return bytes(out)


def _open(archive: bytes) -> tuple[int, int, bytes, dict[str, bytes]]:
    if archive[:4] != MAGIC:
        raise ValueError("bad magic")
    pos = 4
    mode = archive[pos]
    pos += 1
    total_size = struct.unpack(">Q", archive[pos:pos + 8])[0]
    pos += 8
    total_hash = archive[pos:pos + 32]
    pos += 32
    count, pos = _ruvar(archive, pos)
    specs = []
    for _ in range(count):
        cid = archive[pos]
        pos += 1
        raw_len, pos = _ruvar(archive, pos)
        comp_len, pos = _ruvar(archive, pos)
        specs.append((cid, raw_len, comp_len))
    bodies = {}
    for cid, raw_len, comp_len in specs:
        comp = archive[pos:pos + comp_len]
        pos += comp_len
        raw = _unlz(comp)
        if len(raw) != raw_len:
            raise ValueError("channel size mismatch")
        bodies[CHANNEL_NAME[cid]] = raw
    return mode, total_size, total_hash, bodies


def _typed_archive(original: bytes, mode: int) -> bytes | None:
    work = original
    if mode == MODE_TOPIC:
        work = _topic_reorder(original)
        if work is None:
            return None
        restored = _restore_id_order(work)
        if restored != original:
            return None
    if _has_collision(work):
        return None
    scaffold, text_parts, atoms = _extract(work)
    if _reassemble(scaffold, text_parts, atoms) != work:
        return None
    bodies = {
        "scaffold": _op_encode(scaffold),
        "text": _pack_text(text_parts),
        "atoms": _pack_atoms(atoms),
    }
    return _build(mode, bodies, original)


def compress(data: bytes) -> bytes:
    global _S
    candidates = []
    for name, mode in (("typed", MODE_TYPED), ("topic", MODE_TOPIC)):
        arch = _typed_archive(data, mode)
        if arch is not None:
            candidates.append((name, arch))
    if not candidates:
        candidates.append(("literal", _build(MODE_LITERAL, {"literal": data}, data)))
    name, best = min(candidates, key=lambda x: len(x[1]))
    _S = {"mode": name, "archive": len(best), "candidates": {n: len(a) for n, a in candidates}}
    return best


def decompress(archive: bytes) -> bytes:
    mode, total_size, total_hash, bodies = _open(archive)
    if mode == MODE_LITERAL:
        out = bodies["literal"]
    elif mode in (MODE_TYPED, MODE_TOPIC):
        scaffold = _op_decode(bodies["scaffold"])
        text_parts = _unpack_text(bodies["text"])
        atoms = _unpack_atoms(bodies["atoms"])
        out = _reassemble(scaffold, text_parts, atoms)
        if mode == MODE_TOPIC:
            restored = _restore_id_order(out)
            if restored is None:
                raise ValueError("cannot restore page order")
            out = restored
    else:
        raise ValueError("bad mode")
    if len(out) != total_size:
        raise ValueError("total size mismatch")
    if _sha(out) != total_hash:
        raise ValueError("total hash mismatch")
    return out


def stats() -> dict:
    return _S
