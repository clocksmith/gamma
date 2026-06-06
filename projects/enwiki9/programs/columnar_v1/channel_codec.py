"""channel_codec — per-channel lzma + outer-archive layout.

Phase 1 codec: each channel is serialized as (4B count, then per-value
4B length + bytes), then independently compressed with lzma --extreme -9.
The archive concatenates: 4B manifest_len + manifest + per-channel
(4B inner_len + inner_bytes), then wraps the whole thing in one outer
lzma. Outer lzma's job is mostly to compress the manifest and framing;
inner lzmas already entropy-coded their channel.

A "scaffold" channel always exists (it's the XML structure with sentinels
substituted in). In Phase 1, atom channels are: title, id, timestamp,
username, ip, comment. The decoder verifies each channel's sha256
before releasing any bytes.
"""

from __future__ import annotations

import lzma
import struct

import archive_manifest as M
import xml_parser as XP

PRESET = 9 | lzma.PRESET_EXTREME


def serialize_atoms(values: list[bytes]) -> bytes:
    out = bytearray(struct.pack(">I", len(values)))
    for v in values:
        out.extend(struct.pack(">I", len(v)))
        out.extend(v)
    return bytes(out)


def parse_atoms(buf: bytes) -> list[bytes]:
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
        raise ValueError(f"atom-channel parse mismatch: {pos} != {len(buf)}")
    return out


def build_archive(
    mode: str,
    channel_bodies: dict[str, bytes],
    total_input_size: int,
    total_input_hash: str,
) -> bytes:
    """Single monolithic XZ stream over sequentially-concatenated columns.

    The encoder writes channels in `channel_bodies` insertion order. The
    manifest records that order; the decoder reads in manifest order.
    Different modes choose different channel sets — Phase 1 has 7
    channels, Phase 2 has 9, Phase 2A has 11, Phase 3 has 24 (XML +
    transposed template/wikilink columns). lzma operates over the whole
    concatenated buffer in one pass, so per-stream header overhead
    (~1-2 KB per channel) is paid only once.
    """
    entries: list[dict] = []
    big_buffer = bytearray()
    for name, body in channel_bodies.items():
        entries.append(
            {
                "name": name,
                "raw_size": len(body),
                "hash": M.hash_hex(body),
            }
        )
        big_buffer.extend(body)

    manifest = M.build_manifest(
        mode, total_input_size, total_input_hash, entries
    )
    mbytes = M.manifest_to_bytes(manifest)

    out = bytearray()
    out.extend(struct.pack(">I", len(mbytes)))
    out.extend(mbytes)
    out.extend(big_buffer)
    return lzma.compress(bytes(out), preset=PRESET)


def open_archive(arch: bytes) -> tuple[dict, dict[str, bytes]]:
    raw = lzma.decompress(arch)
    pos = 0
    (mlen,) = struct.unpack(">I", raw[pos : pos + 4])
    pos += 4
    manifest = M.manifest_from_bytes(raw[pos : pos + mlen])
    pos += mlen
    channel_bodies: dict[str, bytes] = {}
    for entry in manifest["channels"]:
        size = entry["raw_size"]
        body = raw[pos : pos + size]
        pos += size
        if M.hash_hex(body) != entry["hash"]:
            raise ValueError(
                f"channel hash mismatch: {entry['name']} expected "
                f"{entry['hash']} got {M.hash_hex(body)}"
            )
        if len(body) != size:
            raise ValueError(
                f"channel size mismatch: {entry['name']} expected "
                f"{size} got {len(body)}"
            )
        channel_bodies[entry["name"]] = body
    if pos != len(raw):
        raise ValueError(
            f"trailing bytes after channels: pos={pos} buf_len={len(raw)}"
        )
    return manifest, channel_bodies
