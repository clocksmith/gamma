"""Exact self-trained URL-host dictionary transform for WikiIR-MDL.

The transform leaves the first occurrence of every URL host in the literal
stream.  Once a host has appeared, later occurrences use an escaped reference
to its decoder-rebuilt insertion-order identifier.  URL paths, schemes,
punctuation, and all non-URL bytes remain literal.  Thus the dictionary has no
static payload and no lookahead: encoder and decoder learn the same hosts while
walking already reconstructed bytes.
"""

from __future__ import annotations

import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WUH1"
MODE_LITERAL = 0
MODE_HOSTS = 1
ESCAPE = 0
ESCAPED_ZERO = 0
HOST_REF = 1

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


def _is_host_byte(value: int) -> bool:
    return value not in b" \t\r\n\f\v/][<>{}\"|"


def _scan_hosts(data: bytes) -> tuple[tuple[int, int, bytes], ...]:
    rows: list[tuple[int, int, bytes]] = []
    position = 0
    while position < len(data):
        http = data.find(b"http://", position)
        https = data.find(b"https://", position)
        starts = [value for value in (http, https) if value >= 0]
        if not starts:
            break
        start = min(starts)
        host_start = start + (len(b"https://") if data.startswith(b"https://", start) else len(b"http://"))
        end = host_start
        while end < len(data) and _is_host_byte(data[end]):
            end += 1
        if end > host_start:
            rows.append((host_start, end, data[host_start:end]))
        position = max(end, start + 1)
    return tuple(rows)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    seen: dict[bytes, int] = {}
    output = bytearray(MAGIC)
    source_position = 0
    reference_count = 0
    referenced_source_bytes = 0
    learned_hosts = 0
    for start, end, host in _scan_hosts(data):
        host_id = seen.get(host)
        if host_id is None:
            seen[host] = len(seen)
            learned_hosts += 1
            continue
        output.extend(_escape(data[source_position:start]))
        output.extend((ESCAPE, HOST_REF))
        output.extend(_varint(host_id))
        source_position = end
        reference_count += 1
        referenced_source_bytes += len(host)
    output.extend(_escape(data[source_position:]))
    stats: dict[str, int | str] = {
        "urls_parsed": len(_scan_hosts(data)),
        "learned_hosts": learned_hosts,
        "host_references": reference_count,
        "referenced_source_bytes": referenced_source_bytes,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }
    return bytes(output), stats


class _DecoderHostState:
    def __init__(self) -> None:
        self.hosts: list[bytes] = []
        self.host_ids: dict[bytes, int] = {}
        self.output = bytearray()
        self.window = bytearray()
        self.in_host = False
        self.host = bytearray()

    def _finish_host(self) -> None:
        if self.host and bytes(self.host) not in self.host_ids:
            value = bytes(self.host)
            self.host_ids[value] = len(self.hosts)
            self.hosts.append(value)
        self.host.clear()
        self.in_host = False

    def feed(self, value: int) -> None:
        self.output.append(value)
        if self.in_host:
            if _is_host_byte(value):
                self.host.append(value)
                return
            self._finish_host()
        self.window.append(value)
        if len(self.window) > len(b"https://"):
            del self.window[0]
        if self.window.endswith(b"http://") or self.window.endswith(b"https://"):
            self.in_host = True
            self.host.clear()

    def finish(self) -> None:
        if self.in_host:
            self._finish_host()


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid WikiIR URL-host magic")
    state = _DecoderHostState()
    position = len(MAGIC)
    while position < len(stream):
        value = stream[position]
        position += 1
        if value != ESCAPE:
            state.feed(value)
            continue
        if position >= len(stream):
            raise ValueError("truncated URL-host escape")
        opcode = stream[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            state.feed(ESCAPE)
        elif opcode == HOST_REF:
            if not state.in_host or state.host:
                raise ValueError("URL-host reference outside host start")
            host_id, position = _read_varint(stream, position)
            if host_id >= len(state.hosts):
                raise ValueError("unknown URL-host reference")
            for host_byte in state.hosts[host_id]:
                state.feed(host_byte)
        else:
            raise ValueError("invalid URL-host escape")
    state.finish()
    return bytes(state.output)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("WikiIR URL-host internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    host_archive = lzma.compress(ir, preset=PRESET)
    use_hosts = len(host_archive) < len(literal_archive)
    selected = host_archive if use_hosts else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "host_archive_bytes": len(host_archive),
        "host_archive_gain_before_mode_bytes": len(literal_archive) - len(host_archive),
        "selected_mode": "hosts" if use_hosts else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes((MODE_HOSTS if use_hosts else MODE_LITERAL,)) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty WikiIR URL-host archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_HOSTS:
        return decode_ir(decoded)
    raise ValueError("invalid WikiIR URL-host representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
