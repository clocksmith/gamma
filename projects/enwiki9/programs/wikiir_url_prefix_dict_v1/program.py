"""Exact causal URL host-plus-first-path-prefix transform for WikiIR-MDL.

The first occurrence of each host and ``host/first-segment`` remains literal.
Later URLs may reference either dictionary, whose insertion order is rebuilt
from bytes the decoder has already produced. Schemes, later path components,
punctuation, and all non-URL bytes remain literal.
"""

from __future__ import annotations

import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WUP1"
MODE_LITERAL = 0
MODE_PREFIXES = 1
ESCAPE = 0
ESCAPED_ZERO = 0
HOST_REF = 1
PREFIX_REF = 2

_LAST_STATS: dict[str, int | str | bool] = {}


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _read_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if position >= len(data) or shift > 63:
            raise ValueError("invalid or truncated varint")
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, position
        shift += 7


def _escape(data: bytes) -> bytes:
    return data.replace(b"\x00", b"\x00\x00")


def _is_url_atom(value: int) -> bool:
    return value not in b" \t\r\n\f\v/][<>{}\"|"


def _scan_urls(data: bytes) -> tuple[tuple[int, int, int, bytes, bytes], ...]:
    rows: list[tuple[int, int, int, bytes, bytes]] = []
    position = 0
    while position < len(data):
        starts = [
            value
            for value in (
                data.find(b"http://", position),
                data.find(b"https://", position),
            )
            if value >= 0
        ]
        if not starts:
            break
        scheme_start = min(starts)
        host_start = scheme_start + (
            len(b"https://")
            if data.startswith(b"https://", scheme_start)
            else len(b"http://")
        )
        host_end = host_start
        while host_end < len(data) and _is_url_atom(data[host_end]):
            host_end += 1
        host = data[host_start:host_end]
        prefix_end = host_end
        if host and host_end < len(data) and data[host_end] == ord("/"):
            candidate_end = host_end + 1
            while candidate_end < len(data) and _is_url_atom(data[candidate_end]):
                candidate_end += 1
            if candidate_end > host_end + 1:
                prefix_end = candidate_end
        prefix = data[host_start:prefix_end]
        if host:
            rows.append((host_start, host_end, prefix_end, host, prefix))
        position = max(prefix_end, scheme_start + 1)
    return tuple(rows)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    hosts: dict[bytes, int] = {}
    prefixes: dict[bytes, int] = {}
    output = bytearray(MAGIC)
    source_position = 0
    host_references = 0
    prefix_references = 0
    referenced_source_bytes = 0
    rows = _scan_urls(data)
    for host_start, host_end, prefix_end, host, prefix in rows:
        prefix_id = prefixes.get(prefix)
        host_id = hosts.get(host)
        if prefix != host and prefix_id is not None:
            output.extend(_escape(data[source_position:host_start]))
            output.extend((ESCAPE, PREFIX_REF))
            output.extend(_varint(prefix_id))
            source_position = prefix_end
            prefix_references += 1
            referenced_source_bytes += len(prefix)
        elif host_id is not None:
            output.extend(_escape(data[source_position:host_start]))
            output.extend((ESCAPE, HOST_REF))
            output.extend(_varint(host_id))
            source_position = host_end
            host_references += 1
            referenced_source_bytes += len(host)
        hosts.setdefault(host, len(hosts))
        prefixes.setdefault(prefix, len(prefixes))
    output.extend(_escape(data[source_position:]))
    stats: dict[str, int | str] = {
        "urls_parsed": len(rows),
        "learned_hosts": len(hosts),
        "learned_prefixes": len(prefixes),
        "host_references": host_references,
        "prefix_references": prefix_references,
        "referenced_source_bytes": referenced_source_bytes,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }
    return bytes(output), stats


class _DecoderUrlState:
    def __init__(self) -> None:
        self.hosts: list[bytes] = []
        self.host_ids: dict[bytes, int] = {}
        self.prefixes: list[bytes] = []
        self.prefix_ids: dict[bytes, int] = {}
        self.output = bytearray()
        self.window = bytearray()
        self.in_host = False
        self.in_first_segment = False
        self.host = bytearray()
        self.prefix = bytearray()
        self.segment_bytes = 0

    def _remember_host(self) -> None:
        value = bytes(self.host)
        if value and value not in self.host_ids:
            self.host_ids[value] = len(self.hosts)
            self.hosts.append(value)

    def _finish_url_prefix(self) -> None:
        self._remember_host()
        value = bytes(self.prefix) if self.segment_bytes else bytes(self.host)
        if value and value not in self.prefix_ids:
            self.prefix_ids[value] = len(self.prefixes)
            self.prefixes.append(value)
        self.in_host = False
        self.in_first_segment = False
        self.host.clear()
        self.prefix.clear()
        self.segment_bytes = 0

    def _scan_scheme(self, value: int) -> None:
        self.window.append(value)
        if len(self.window) > len(b"https://"):
            del self.window[0]
        if self.window.endswith(b"http://") or self.window.endswith(b"https://"):
            self.in_host = True
            self.host.clear()
            self.prefix.clear()
            self.segment_bytes = 0

    def feed(self, value: int) -> None:
        self.output.append(value)
        if self.in_host:
            if _is_url_atom(value):
                self.host.append(value)
                self.prefix.append(value)
                return
            self._remember_host()
            if value == ord("/") and self.host:
                self.prefix.append(value)
                self.in_host = False
                self.in_first_segment = True
                return
            self._finish_url_prefix()
            self._scan_scheme(value)
            return
        if self.in_first_segment:
            if _is_url_atom(value):
                self.prefix.append(value)
                self.segment_bytes += 1
                return
            self._finish_url_prefix()
            self._scan_scheme(value)
            return
        self._scan_scheme(value)

    def finish(self) -> None:
        if self.in_host or self.in_first_segment:
            self._finish_url_prefix()


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid WikiIR URL-prefix magic")
    state = _DecoderUrlState()
    position = len(MAGIC)
    while position < len(stream):
        value = stream[position]
        position += 1
        if value != ESCAPE:
            state.feed(value)
            continue
        if position >= len(stream):
            raise ValueError("truncated URL-prefix escape")
        opcode = stream[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            state.feed(ESCAPE)
            continue
        reference_id, position = _read_varint(stream, position)
        if not state.in_host or state.host:
            raise ValueError("URL reference outside host start")
        if opcode == HOST_REF:
            if reference_id >= len(state.hosts):
                raise ValueError("unknown URL-host reference")
            referenced = state.hosts[reference_id]
        elif opcode == PREFIX_REF:
            if reference_id >= len(state.prefixes):
                raise ValueError("unknown URL-prefix reference")
            referenced = state.prefixes[reference_id]
        else:
            raise ValueError("invalid URL-prefix escape")
        for referenced_byte in referenced:
            state.feed(referenced_byte)
    state.finish()
    return bytes(state.output)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("WikiIR URL-prefix internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    prefix_archive = lzma.compress(ir, preset=PRESET)
    use_prefixes = len(prefix_archive) < len(literal_archive)
    selected = prefix_archive if use_prefixes else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "prefix_archive_bytes": len(prefix_archive),
        "prefix_archive_gain_before_mode_bytes": len(literal_archive)
        - len(prefix_archive),
        "selected_mode": "prefixes" if use_prefixes else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes((MODE_PREFIXES if use_prefixes else MODE_LITERAL,)) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty WikiIR URL-prefix archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_PREFIXES:
        return decode_ir(decoded)
    raise ValueError("invalid WikiIR URL-prefix representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
