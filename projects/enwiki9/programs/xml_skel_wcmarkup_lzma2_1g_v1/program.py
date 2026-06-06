"""xml_skel_wcmarkup_lzma2_1g_v1 — Phase 1_WC + extended-markup wordcode.

Typed MediaWiki XML field extraction (id, title, timestamp, username, ip,
comment) + wordcode pre-pass on the prose-heavy scaffold + single
monolithic LZMA2 with 1 GiB dict_size over the concatenated typed buffer.

The larger dict matters at >64 MB input scope where Python lzma's default
64 MB dict starts missing matches; below that it's identical to the
default preset.

This is the lean form of the Phase 1_WC architecture from columnar_v1
with the fallback modes (Phase 2A, Phase 4) removed and all helper
modules inlined into program.py to minimize program_size. Roundtrip is
hash-validated end to end. Sentinel-collision check at the top falls
through to a single-channel literal encoding that always roundtrips.

Architecture:
  bytes
    -> XML field extract (atom channels + scaffold-with-sentinels)
    -> wordcode pack on scaffold (top-K word substitution)
    -> manifest + concatenated channel buffer
    -> single lzma --extreme -9 pass

The wordcode pack is the type-aware codec for the prose channel; lzma
is the entropy coder for everything (scaffold + small atom channels in
one stream so per-stream framing is paid once).
"""

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

# wordcode constants
WC_ESC = 0x02
WC_CODE_BASE = 0x80
WC_MAX_K = 128
WC_MIN_WORD_LEN = 3
WC_MAX_WORD_LEN = 32
WC_MIN_FREQ = 2
# Extended token regex: alphabetic words [A-Za-z]{3,32} OR wiki markup tokens
# ([[, ]], {{, }}, ==+, '''+, ''). The picker scores each token by save value
# so only frequent enough wiki markup tokens earn a code slot.
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


# ─── wordcode pack/unpack (prose-heavy scaffold codec) ───

def _wc_pick(data: bytes) -> list[bytes]:
    counts: dict[bytes, int] = {}
    for m in WC_WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    scored = []
    for w, f in counts.items():
        if f < WC_MIN_FREQ:
            continue
        save = f * (len(w) - 1) - (1 + len(w))
        if save > 0:
            scored.append((save, w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:WC_MAX_K]]


def _wc_escape(chunk: bytes) -> bytes:
    if not any(b == WC_ESC or b >= WC_CODE_BASE for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b == WC_ESC or b >= WC_CODE_BASE:
            out.append(WC_ESC)
        out.append(b)
    return bytes(out)


def _wc_substitute(data: bytes, words: list[bytes]) -> bytes:
    if not words:
        return _wc_escape(data)
    code_map = {w: bytes([WC_CODE_BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    parts = []
    pos = 0
    for m in pat.finditer(data):
        if m.start() > pos:
            parts.append(_wc_escape(data[pos : m.start()]))
        parts.append(code_map[m.group(0)])
        pos = m.end()
    if pos < len(data):
        parts.append(_wc_escape(data[pos:]))
    return b"".join(parts)


def _wc_expand(stream: bytes, words: list[bytes]) -> bytes:
    out = bytearray()
    pos = 0
    n = len(stream)
    while pos < n:
        b = stream[pos]
        if b == WC_ESC:
            pos += 1
            out.append(stream[pos])
            pos += 1
        elif b >= WC_CODE_BASE:
            idx = b - WC_CODE_BASE
            out.extend(words[idx])
            pos += 1
        else:
            out.append(b)
            pos += 1
    return bytes(out)


def _wc_pack(data: bytes) -> bytes:
    words = _wc_pick(data)
    body = _wc_substitute(data, words)
    header = bytearray()
    header.append(len(words))
    for w in words:
        header.append(len(w))
        header.extend(w)
    return struct.pack(">I", len(header)) + bytes(header) + body


def _wc_unpack(packed: bytes) -> bytes:
    (hlen,) = struct.unpack(">I", packed[:4])
    header = packed[4 : 4 + hlen]
    body = packed[4 + hlen :]
    k = header[0]
    pos = 1
    words = []
    for _ in range(k):
        L = header[pos]
        pos += 1
        words.append(header[pos : pos + L])
        pos += L
    return _wc_expand(body, words)


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

def compress(data: bytes) -> bytes:
    total_size = len(data)
    total_hash = _hash_hex(data)
    if _has_sentinel_collision(data):
        bodies = {"scaffold": data}
        for n in CHANNEL_NAMES:
            bodies[n] = _serialize_atoms([])
        return _build_archive(MODE_LITERAL, bodies, total_size, total_hash)
    scaffold, channels = _extract_xml(data)
    if _reassemble_xml(scaffold, channels) != data:
        bodies = {"scaffold": data}
        for n in CHANNEL_NAMES:
            bodies[n] = _serialize_atoms([])
        return _build_archive(MODE_LITERAL, bodies, total_size, total_hash)
    packed_scaffold = _wc_pack(scaffold)
    if _wc_unpack(packed_scaffold) != scaffold:
        bodies = {"scaffold": data}
        for n in CHANNEL_NAMES:
            bodies[n] = _serialize_atoms([])
        return _build_archive(MODE_LITERAL, bodies, total_size, total_hash)
    bodies = {"scaffold": packed_scaffold}
    for n in CHANNEL_NAMES:
        bodies[n] = _serialize_atoms(channels[n])
    return _build_archive(MODE_TYPED, bodies, total_size, total_hash)


def decompress(arch: bytes) -> bytes:
    manifest, bodies = _open_archive(arch)
    mode = manifest["mode"]
    if mode == MODE_LITERAL:
        out = bodies["scaffold"]
    elif mode == MODE_TYPED:
        scaffold = _wc_unpack(bodies["scaffold"])
        channels = {n: _parse_atoms(bodies[n]) for n in CHANNEL_NAMES}
        out = _reassemble_xml(scaffold, channels)
    else:
        raise ValueError(f"unknown mode: {mode}")
    if len(out) != manifest["total_input_size"]:
        raise ValueError("size mismatch")
    if _hash_hex(out) != manifest["total_input_hash"]:
        raise ValueError("total hash mismatch")
    return out
