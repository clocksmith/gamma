"""iph_lzma_v1 — Intent-Posterior-Hashed compression: typed artifacts +
per-channel lzma + hash-validated manifest + strict parse validation.

Architecture mirrors the dream/ intent-posterior contract
(`schemas/intent-posterior.json`):
  Free-form input (enwik9 bytes) → typed artifacts (pages, revisions,
  fields) → channeled compression. Manifest carries provenance (schema
  version, tokenizer version, channel hashes). Encoder runs strict parse
  validation: simulates decode, byte-compares to input, falls back to a
  single-channel literal mode on any mismatch — the archive cannot be
  emitted with a hash that disagrees with reality.

Channels (typed atom streams):
  - scaffold     : XML/structural bytes with field values replaced by
                   sentinels; the "shape" carrier
  - titles       : <title>X</title> values
  - ids          : every <id>X</id> value (page IDs + revision IDs +
                   contributor IDs, in document order)
  - timestamps   : <timestamp>X</timestamp> values
  - usernames    : <username>X</username> values
  - ips          : <ip>X</ip> values
  - comments     : <comment>...</comment> values
  - texts        : <text xml:space="preserve">...</text> values (the bulk)

Each channel is independently lzma-compressed. Per-channel sha256 hash is
recorded in the manifest. Decoder verifies all hashes match before
emitting any bytes.

Strict parse validation:
  - sentinels are 4-byte sequences that MUST NOT appear in input; if any
    do, we abort typed mode and fall back to literal scaffold (whole input
    in scaffold channel, all others empty)
  - after extraction, the encoder simulates a decode and asserts the
    reconstructed bytes match the input exactly; otherwise falls back

Archive layout (all under one outer lzma):
  4B  manifest_len
  N   manifest (JSON, includes schema_version, tokenizer_version, mode,
                channels with name/hash/count, total_input_size,
                total_input_hash)
  per-channel inner lzma payloads, in manifest channel order:
    4B inner_len, inner_len bytes (lzma-compressed channel)

Provenance fields in manifest:
  schema_version : invariant for archive layout
  tokenizer_version : invariant for sentinel/regex set
  mode : "typed_v1" or "literal_fallback"
  total_input_size : exact byte length of original
  total_input_hash : sha256 hex of original (full 64 chars for verifier)
  channels[name].hash : sha256 hex of channel's pre-compression bytes
"""

from __future__ import annotations

import hashlib
import json
import lzma
import re
import struct

PRESET = 9 | lzma.PRESET_EXTREME
SCHEMA_VERSION = 1
TOKENIZER_VERSION = 1

# Sentinels — 4 bytes each, must be unique to channels and absent from input.
SENT = {
    "titles":     b"\x00\x00\xFE\xF1",
    "ids":        b"\x00\x00\xFE\xF2",
    "timestamps": b"\x00\x00\xFE\xF4",
    "usernames":  b"\x00\x00\xFE\xF5",
    "ips":        b"\x00\x00\xFE\xF6",
    "comments":   b"\x00\x00\xFE\xF8",
    "texts":      b"\x00\x00\xFE\xF9",
}

# Channel order: scaffold first (the shape carrier), then atom channels in
# the order the encoder/decoder uses for emission.
CHANNEL_ORDER = ["scaffold", "titles", "ids", "timestamps",
                 "usernames", "ips", "comments", "texts"]

# Compile patterns. Order matters for extraction: extract texts first
# (most specific, multi-line); then comments; then atomic fields.
_TEXT_RE      = re.compile(rb'(<text xml:space="preserve">)(.*?)(</text>)', re.DOTALL)
_COMMENT_RE   = re.compile(rb'(<comment>)(.*?)(</comment>)', re.DOTALL)
_TITLE_RE     = re.compile(rb'(<title>)([^<]*)(</title>)')
_TIMESTAMP_RE = re.compile(rb'(<timestamp>)([^<]*)(</timestamp>)')
_USERNAME_RE  = re.compile(rb'(<username>)([^<]*)(</username>)')
_IP_RE        = re.compile(rb'(<ip>)([^<]*)(</ip>)')
_ID_RE        = re.compile(rb'(<id>)([^<]*)(</id>)')


def _extract(data: bytes, regex: re.Pattern, sentinel: bytes) -> tuple[bytes, list[bytes]]:
    """Replace each match's middle group with `sentinel`; return new bytes
    and the list of captured values in order."""
    captured: list[bytes] = []

    def _repl(m: re.Match) -> bytes:
        captured.append(m.group(2))
        return m.group(1) + sentinel + m.group(3)

    return regex.sub(_repl, data), captured


def _serialize_atoms(values: list[bytes]) -> bytes:
    """4B count + per-value (4B length + bytes)."""
    out = bytearray(struct.pack(">I", len(values)))
    for v in values:
        out.extend(struct.pack(">I", len(v)))
        out.extend(v)
    return bytes(out)


def _parse_atoms(buf: bytes) -> list[bytes]:
    pos = 0
    (n,) = struct.unpack(">I", buf[pos : pos + 4])
    pos += 4
    out: list[bytes] = []
    for _ in range(n):
        (L,) = struct.unpack(">I", buf[pos : pos + 4])
        pos += 4
        out.append(buf[pos : pos + L])
        pos += L
    if pos != len(buf):
        raise ValueError(f"atom-channel parse: {pos} != {len(buf)}")
    return out


def _hash_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _try_typed_split(data: bytes) -> dict[str, bytes] | None:
    """Returns dict of channel-name -> channel-bytes, or None to fall back."""
    for name, sent in SENT.items():
        if sent in data:
            return None  # sentinel collision; literal fallback
    scaffold = data
    extracts: dict[str, list[bytes]] = {}
    # Order matters: extract longest/most specific first.
    for name, regex in (
        ("texts", _TEXT_RE),
        ("comments", _COMMENT_RE),
        ("titles", _TITLE_RE),
        ("timestamps", _TIMESTAMP_RE),
        ("usernames", _USERNAME_RE),
        ("ips", _IP_RE),
        ("ids", _ID_RE),
    ):
        scaffold, captured = _extract(scaffold, regex, SENT[name])
        extracts[name] = captured
    return {
        "scaffold": scaffold,
        **{name: _serialize_atoms(extracts[name]) for name in extracts},
    }


def _typed_decode(channels: dict[str, bytes]) -> bytes:
    """Walk scaffold, when sentinel encountered emit next value from
    that channel."""
    scaffold = channels["scaffold"]
    iters = {
        name: iter(_parse_atoms(channels[name])) for name in SENT
    }
    out = bytearray()
    pos = 0
    n = len(scaffold)
    sentinel_to_name = {sent: name for name, sent in SENT.items()}
    while pos < n:
        match_name = None
        for name, sent in SENT.items():
            if pos + 4 <= n and scaffold[pos : pos + 4] == sent:
                match_name = name
                break
        if match_name is None:
            out.append(scaffold[pos])
            pos += 1
        else:
            try:
                value = next(iters[match_name])
            except StopIteration:
                raise ValueError(
                    f"channel underflow: {match_name} at scaffold pos {pos}"
                )
            out.extend(value)
            pos += 4
    # Drain check: every channel iter must be exhausted.
    for name, it in iters.items():
        try:
            next(it)
            raise ValueError(f"channel overflow: {name} has unconsumed values")
        except StopIteration:
            pass
    return bytes(out)


def _strict_validate(data: bytes, channels: dict[str, bytes]) -> bool:
    try:
        return _typed_decode(channels) == data
    except Exception:
        return False


def _build_archive(channels: dict[str, bytes], mode: str,
                   total_size: int, total_hash: str) -> bytes:
    manifest: dict = {
        "schema_version": SCHEMA_VERSION,
        "tokenizer_version": TOKENIZER_VERSION,
        "mode": mode,
        "total_input_size": total_size,
        "total_input_hash": total_hash,
        "channels": [],
    }
    inner_payloads: list[bytes] = []
    for name in CHANNEL_ORDER:
        body = channels.get(name, b"")
        manifest["channels"].append(
            {"name": name, "raw_size": len(body), "hash": _hash_hex(body)}
        )
        inner_payloads.append(lzma.compress(body, preset=PRESET))

    mbytes = json.dumps(manifest, separators=(",", ":")).encode()
    out = bytearray()
    out.extend(struct.pack(">I", len(mbytes)))
    out.extend(mbytes)
    for p in inner_payloads:
        out.extend(struct.pack(">I", len(p)))
        out.extend(p)
    # Single outer lzma to compress the manifest + per-channel framing
    # together. The per-channel inner lzmas are already entropy-coded;
    # outer lzma mostly catches the manifest + framing.
    return lzma.compress(bytes(out), preset=PRESET)


def _open_archive(arch: bytes) -> tuple[dict, dict[str, bytes]]:
    raw = lzma.decompress(arch)
    pos = 0
    (mlen,) = struct.unpack(">I", raw[pos : pos + 4])
    pos += 4
    manifest = json.loads(raw[pos : pos + mlen])
    pos += mlen
    channels: dict[str, bytes] = {}
    for entry in manifest["channels"]:
        (plen,) = struct.unpack(">I", raw[pos : pos + 4])
        pos += 4
        inner = raw[pos : pos + plen]
        pos += plen
        body = lzma.decompress(inner)
        if _hash_hex(body) != entry["hash"]:
            raise ValueError(
                f"channel hash mismatch: {entry['name']} "
                f"expected {entry['hash']} got {_hash_hex(body)}"
            )
        if len(body) != entry["raw_size"]:
            raise ValueError(
                f"channel size mismatch: {entry['name']} "
                f"expected {entry['raw_size']} got {len(body)}"
            )
        channels[entry["name"]] = body
    return manifest, channels


def compress(data: bytes) -> bytes:
    total_size = len(data)
    total_hash = _hash_hex(data)
    typed = _try_typed_split(data)
    if typed is not None and _strict_validate(data, typed):
        return _build_archive(typed, "typed_v1", total_size, total_hash)
    # Strict parse validation failed → literal fallback. Scaffold = whole
    # input; all atom channels empty.
    fallback = {
        "scaffold": data,
        **{name: _serialize_atoms([]) for name in SENT},
    }
    return _build_archive(fallback, "literal_fallback", total_size, total_hash)


def decompress(arch: bytes) -> bytes:
    manifest, channels = _open_archive(arch)
    if manifest["mode"] == "typed_v1":
        out = _typed_decode(channels)
    elif manifest["mode"] == "literal_fallback":
        out = channels["scaffold"]
    else:
        raise ValueError(f"unknown mode: {manifest['mode']}")
    if len(out) != manifest["total_input_size"]:
        raise ValueError(
            f"size mismatch: got {len(out)} expected {manifest['total_input_size']}"
        )
    if _hash_hex(out) != manifest["total_input_hash"]:
        raise ValueError("total input hash mismatch")
    return out
