"""xml_skel_wc3tier_jc_lzma2_1g_v1 — wc3tier with shared-vocab comment co-wordcoding."""

from __future__ import annotations

import hashlib
import json
import lzma
import re
import struct

PRESET = 9 | lzma.PRESET_EXTREME
_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": PRESET, "dict_size": 1 << 30}]
SCHEMA_VERSION = 1
MODE_TYPED = "typed_v1"
MODE_LITERAL = "literal"

SENT = {
    "title":     b"\x00\x00\xFE\xF1",
    "id":        b"\x00\x00\xFE\xF2",
    "timestamp": b"\x00\x00\xFE\xF4",
    "username":  b"\x00\x00\xFE\xF5",
    "ip":        b"\x00\x00\xFE\xF6",
    "comment":   b"\x00\x00\xFE\xF8",
}
CHANNEL_NAMES = ["title", "id", "timestamp", "username", "ip", "comment"]
ARCHIVE_ORDER = ["scaffold"] + CHANNEL_NAMES

_RE_COMMENT   = re.compile(rb"(<comment>)(.*?)(</comment>)", re.DOTALL)
_RE_TITLE     = re.compile(rb"(<title>)([^<]*)(</title>)")
_RE_TIMESTAMP = re.compile(rb"(<timestamp>)([^<]*)(</timestamp>)")
_RE_USERNAME  = re.compile(rb"(<username>)([^<]*)(</username>)")
_RE_IP        = re.compile(rb"(<ip>)([^<]*)(</ip>)")
_RE_ID        = re.compile(rb"(<id>)([^<]*)(</id>)")
_FIELD_REGEX = [
    ("comment", _RE_COMMENT),
    ("title", _RE_TITLE),
    ("timestamp", _RE_TIMESTAMP),
    ("username", _RE_USERNAME),
    ("ip", _RE_IP),
    ("id", _RE_ID),
]

# Wordcode constants
WC_ESC = 0x02              # literal-escape prefix
WC_TWO = 0x03              # 2-byte code prefix
WC_THREE = 0x04            # 3-byte code prefix
WC_CODE_BASE = 0x80        # single-byte code base
WC_K1 = 128                # tier-1 slots (1-byte codes)
WC_K2 = 256                # tier-2 slots (2-byte codes)
WC_K3 = 4096               # tier-3 slot cap (3-byte codes)
WC_MIN_WORD_LEN = 3
WC_MAX_WORD_LEN = 32
WC_MIN_FREQ = 2
WC_WORD_RE = re.compile(
    rb"[A-Za-z]{%d,%d}|\[\[|\]\]|\{\{|\}\}|==+|'''+|''"
    % (WC_MIN_WORD_LEN, WC_MAX_WORD_LEN)
)


def _hash_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _has_sentinel_collision(data: bytes) -> bool:
    return any(s in data for s in SENT.values())


def _extract_xml(data: bytes) -> tuple[bytes, dict[str, list[bytes]]]:
    scaffold = data
    channels: dict[str, list[bytes]] = {n: [] for n in CHANNEL_NAMES}
    for name, rgx in _FIELD_REGEX:
        captured: list[bytes] = []
        sent = SENT[name]
        def repl(m: re.Match, _c=captured, _s=sent) -> bytes:
            _c.append(m.group(2))
            return m.group(1) + _s + m.group(3)
        scaffold = rgx.sub(repl, scaffold)
        channels[name] = captured
    return scaffold, channels


def _reassemble_xml(scaffold: bytes, channels: dict[str, list[bytes]]) -> bytes:
    iters = {n: iter(channels[n]) for n in CHANNEL_NAMES}
    out = bytearray()
    pos = 0
    n = len(scaffold)
    while pos < n:
        match = None
        if pos + 4 <= n:
            window = scaffold[pos : pos + 4]
            for name, sent in SENT.items():
                if window == sent:
                    match = name
                    break
        if match is None:
            out.append(scaffold[pos])
            pos += 1
        else:
            out.extend(next(iters[match]))
            pos += 4
    return bytes(out)


def _serialize_atoms(values: list[bytes]) -> bytes:
    out = bytearray(struct.pack(">I", len(values)))
    for v in values:
        out.extend(struct.pack(">I", len(v)))
        out.extend(v)
    return bytes(out)


def _parse_atoms(buf: bytes) -> list[bytes]:
    pos = 0
    (n,) = struct.unpack(">I", buf[pos : pos + 4])
    pos += 4
    out = []
    for _ in range(n):
        (L,) = struct.unpack(">I", buf[pos : pos + 4])
        pos += 4
        out.append(buf[pos : pos + L])
        pos += L
    return out


# ─── 3-tier wordcode pack/unpack ───

def _wc_pick(data: bytes) -> tuple[list[bytes], list[bytes], list[bytes]]:
    """Greedy tier assignment by save = f*(L-c)-(1+L) at each width c.
    Returns (top1, top2, top3) — disjoint, no token assigned to two tiers."""
    counts: dict[bytes, int] = {}
    for m in WC_WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1

    def pick_at_width(c: int, exclude: set[bytes], cap: int) -> list[bytes]:
        scored = []
        for w, f in counts.items():
            if f < WC_MIN_FREQ or w in exclude:
                continue
            s = f * (len(w) - c) - (1 + len(w))
            if s > 0:
                scored.append((s, w))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [w for _, w in scored[:cap]]

    top1 = pick_at_width(1, set(), WC_K1)
    top2 = pick_at_width(2, set(top1), WC_K2)
    top3 = pick_at_width(3, set(top1) | set(top2), WC_K3)
    return top1, top2, top3


def _wc_escape(chunk: bytes) -> bytes:
    if not any(b in (WC_ESC, WC_TWO, WC_THREE) or b >= WC_CODE_BASE
               for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b in (WC_ESC, WC_TWO, WC_THREE) or b >= WC_CODE_BASE:
            out.append(WC_ESC)
        out.append(b)
    return bytes(out)


def _wc_substitute(data: bytes, top1: list[bytes], top2: list[bytes],
                   top3: list[bytes]) -> bytes:
    code_for: dict[bytes, bytes] = {}
    for i, w in enumerate(top1):
        code_for[w] = bytes([WC_CODE_BASE + i])
    for i, w in enumerate(top2):
        code_for[w] = bytes([WC_TWO, i])
    for i, w in enumerate(top3):
        code_for[w] = bytes([WC_THREE, i >> 8, i & 0xFF])
    if not code_for:
        return _wc_escape(data)
    all_tokens = list(code_for.keys())
    all_tokens.sort(key=lambda x: -len(x))
    pat = re.compile(b"|".join(re.escape(w) for w in all_tokens))
    parts: list[bytes] = []
    pos = 0
    for m in pat.finditer(data):
        if m.start() > pos:
            parts.append(_wc_escape(data[pos : m.start()]))
        parts.append(code_for[m.group(0)])
        pos = m.end()
    if pos < len(data):
        parts.append(_wc_escape(data[pos:]))
    return b"".join(parts)


def _wc_expand(stream: bytes, top1: list[bytes], top2: list[bytes],
               top3: list[bytes]) -> bytes:
    out = bytearray()
    pos = 0
    n = len(stream)
    while pos < n:
        b = stream[pos]
        if b == WC_ESC:
            pos += 1
            out.append(stream[pos])
            pos += 1
        elif b == WC_TWO:
            idx = stream[pos + 1]
            out.extend(top2[idx])
            pos += 2
        elif b == WC_THREE:
            idx = (stream[pos + 1] << 8) | stream[pos + 2]
            out.extend(top3[idx])
            pos += 3
        elif b >= WC_CODE_BASE:
            idx = b - WC_CODE_BASE
            out.extend(top1[idx])
            pos += 1
        else:
            out.append(b)
            pos += 1
    return bytes(out)


def _wc_pack(data: bytes) -> tuple[bytes, list[bytes], list[bytes], list[bytes]]:
    top1, top2, top3 = _wc_pick(data)
    body = _wc_substitute(data, top1, top2, top3)
    header = bytearray()
    header.append(len(top1))
    for w in top1:
        header.append(len(w))
        header.extend(w)
    header.extend(struct.pack(">H", len(top2)))
    for w in top2:
        header.append(len(w))
        header.extend(w)
    header.extend(struct.pack(">H", len(top3)))
    for w in top3:
        header.append(len(w))
        header.extend(w)
    packed = struct.pack(">I", len(header)) + bytes(header) + body
    return packed, top1, top2, top3


def _wc_unpack(packed: bytes) -> tuple[bytes, list[bytes], list[bytes], list[bytes]]:
    (hlen,) = struct.unpack(">I", packed[:4])
    header = packed[4 : 4 + hlen]
    body = packed[4 + hlen :]
    pos = 0
    k1 = header[pos]; pos += 1
    top1 = []
    for _ in range(k1):
        L = header[pos]; pos += 1
        top1.append(header[pos : pos + L]); pos += L
    (k2,) = struct.unpack(">H", header[pos : pos + 2]); pos += 2
    top2 = []
    for _ in range(k2):
        L = header[pos]; pos += 1
        top2.append(header[pos : pos + L]); pos += L
    (k3,) = struct.unpack(">H", header[pos : pos + 2]); pos += 2
    top3 = []
    for _ in range(k3):
        L = header[pos]; pos += 1
        top3.append(header[pos : pos + L]); pos += L
    return _wc_expand(body, top1, top2, top3), top1, top2, top3


def _pack_comment_with_vocab(comment_atoms: list[bytes], top1: list[bytes],
                             top2: list[bytes], top3: list[bytes]) -> bytes:
    concat = b"".join(comment_atoms)
    sub = _wc_substitute(concat, top1, top2, top3)
    out = bytearray()
    out.extend(struct.pack(">I", len(sub)))
    out.extend(sub)
    out.extend(struct.pack(">I", len(comment_atoms)))
    for a in comment_atoms:
        out.extend(struct.pack(">I", len(a)))
    return bytes(out)


def _unpack_comment_with_vocab(buf: bytes, top1: list[bytes],
                               top2: list[bytes], top3: list[bytes]) -> list[bytes]:
    pos = 0
    (sl,) = struct.unpack(">I", buf[pos : pos + 4]); pos += 4
    sub = buf[pos : pos + sl]; pos += sl
    (n,) = struct.unpack(">I", buf[pos : pos + 4]); pos += 4
    lengths = []
    for _ in range(n):
        (L,) = struct.unpack(">I", buf[pos : pos + 4]); pos += 4
        lengths.append(L)
    concat = _wc_expand(sub, top1, top2, top3)
    out = []
    p = 0
    for L in lengths:
        out.append(concat[p : p + L])
        p += L
    return out


# ─── archive build / open ───

def _build_archive(mode: str, channel_bodies: dict[str, bytes],
                   total_size: int, total_hash: str) -> bytes:
    entries = []
    big = bytearray()
    for name in ARCHIVE_ORDER:
        body = channel_bodies.get(name, b"")
        entries.append({"name": name, "raw_size": len(body), "hash": _hash_hex(body)})
        big.extend(body)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "total_input_size": total_size,
        "total_input_hash": total_hash,
        "channels": entries,
    }
    mb = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("ascii")
    out = bytearray()
    out.extend(struct.pack(">I", len(mb)))
    out.extend(mb)
    out.extend(big)
    return lzma.compress(bytes(out), format=lzma.FORMAT_XZ, filters=_FILTERS)


def _open_archive(arch: bytes) -> tuple[dict, dict[str, bytes]]:
    raw = lzma.decompress(arch)
    pos = 0
    (mlen,) = struct.unpack(">I", raw[pos : pos + 4])
    pos += 4
    manifest = json.loads(raw[pos : pos + mlen])
    pos += mlen
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema version mismatch")
    bodies: dict[str, bytes] = {}
    for entry in manifest["channels"]:
        sz = entry["raw_size"]
        body = raw[pos : pos + sz]
        pos += sz
        if _hash_hex(body) != entry["hash"]:
            raise ValueError(f"channel hash mismatch: {entry['name']}")
        bodies[entry["name"]] = body
    return manifest, bodies


# ─── public compress / decompress ───

def _literal_bodies(data: bytes) -> dict[str, bytes]:
    bodies = {"scaffold": data}
    for n in CHANNEL_NAMES:
        bodies[n] = _serialize_atoms([])
    return bodies


def compress(data: bytes) -> bytes:
    total_size = len(data)
    total_hash = _hash_hex(data)
    if _has_sentinel_collision(data):
        return _build_archive(MODE_LITERAL, _literal_bodies(data),
                              total_size, total_hash)
    scaffold, channels = _extract_xml(data)
    if _reassemble_xml(scaffold, channels) != data:
        return _build_archive(MODE_LITERAL, _literal_bodies(data),
                              total_size, total_hash)
    packed_scaffold, top1, top2, top3 = _wc_pack(scaffold)
    rt_scaffold, _, _, _ = _wc_unpack(packed_scaffold)
    if rt_scaffold != scaffold:
        return _build_archive(MODE_LITERAL, _literal_bodies(data),
                              total_size, total_hash)
    # Co-wordcode the comment channel with the shared scaffold vocab.
    packed_comment = _pack_comment_with_vocab(channels["comment"],
                                              top1, top2, top3)
    rt_comment = _unpack_comment_with_vocab(packed_comment, top1, top2, top3)
    if rt_comment != channels["comment"]:
        return _build_archive(MODE_LITERAL, _literal_bodies(data),
                              total_size, total_hash)
    bodies = {"scaffold": packed_scaffold, "comment": packed_comment}
    for n in CHANNEL_NAMES:
        if n == "comment":
            continue
        bodies[n] = _serialize_atoms(channels[n])
    return _build_archive(MODE_TYPED, bodies, total_size, total_hash)


def decompress(arch: bytes) -> bytes:
    manifest, bodies = _open_archive(arch)
    mode = manifest["mode"]
    if mode == MODE_LITERAL:
        out = bodies["scaffold"]
    elif mode == MODE_TYPED:
        scaffold, top1, top2, top3 = _wc_unpack(bodies["scaffold"])
        channels: dict[str, list[bytes]] = {}
        for n in CHANNEL_NAMES:
            if n == "comment":
                channels[n] = _unpack_comment_with_vocab(
                    bodies[n], top1, top2, top3)
            else:
                channels[n] = _parse_atoms(bodies[n])
        out = _reassemble_xml(scaffold, channels)
    else:
        raise ValueError(f"unknown mode: {mode}")
    if len(out) != manifest["total_input_size"]:
        raise ValueError("size mismatch")
    if _hash_hex(out) != manifest["total_input_hash"]:
        raise ValueError("total hash mismatch")
    return out
