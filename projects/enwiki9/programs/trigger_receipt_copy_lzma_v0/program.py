"""Paid fixed-length trigger receipt copies over one identical LZMA backend."""

import lzma
import struct


MAGIC = b"TRCOPY0\0"
PRESET = 9 | lzma.PRESET_EXTREME
ESCAPE = 0
LITERAL_ZERO = 0
COPY = 1
CONTINUATION_BYTES = 32
MAX_KEYS = 8192
MAX_CANDIDATES = 8
MODES = ("RAW", "C0", "E0")
TRIGGERS = (
    b"<timestamp>",
    b"<title>",
    b"[[",
    b"{{",
    b"\n",
    b"|",
    b"=",
)

_LAST_STATS = {}


def _normalized_suffix(data):
    return bytes(byte + 32 if 65 <= byte <= 90 else byte for byte in data[-4:])


class History:
    def __init__(self):
        self.tail = bytearray()

    def observe(self, data):
        self.tail.extend(data)
        if len(self.tail) > 192:
            del self.tail[:-128]

    def trigger(self):
        tail = bytes(self.tail)
        for trigger_id, marker in enumerate(TRIGGERS):
            if tail.endswith(marker):
                return trigger_id, marker
        return None

    def key(self, profile, trigger):
        trigger_id, marker = trigger
        if profile == "C0":
            return (trigger_id,)
        before = bytes(self.tail)[:-len(marker)]
        return trigger_id, _normalized_suffix(before)


class ReceiptMemory:
    def __init__(self):
        self.rows = {}
        self.order = []
        self.cursor = 0

    def get(self, key):
        return tuple(self.rows.get(key, ()))

    def add(self, key, continuation):
        row = self.rows.get(key)
        if row is None:
            if len(self.rows) >= MAX_KEYS:
                while self.cursor < len(self.order):
                    old = self.order[self.cursor]
                    self.cursor += 1
                    if old in self.rows:
                        del self.rows[old]
                        break
                if self.cursor > 4096 and self.cursor * 2 > len(self.order):
                    self.order = self.order[self.cursor:]
                    self.cursor = 0
            row = []
            self.rows[key] = row
            self.order.append(key)
        row.append(continuation)
        if len(row) > MAX_CANDIDATES:
            del row[0]


def _emit_literal(output, byte):
    if byte == ESCAPE:
        output.extend((ESCAPE, LITERAL_ZERO))
    else:
        output.append(byte)


def _read_literal(stream, position):
    if position >= len(stream):
        raise ValueError("truncated receipt IR literal")
    byte = stream[position]
    position += 1
    if byte != ESCAPE:
        return byte, position
    if position >= len(stream) or stream[position] != LITERAL_ZERO:
        raise ValueError("invalid receipt IR literal escape")
    return 0, position + 1


def _encode_ir(data, profile):
    history = History()
    memory = ReceiptMemory()
    output = bytearray()
    position = 0
    opportunities = 0
    wakes = 0
    copies = 0
    copied_bytes = 0
    while position < len(data):
        byte = data[position]
        position += 1
        _emit_literal(output, byte)
        history.observe(bytes((byte,)))
        trigger = history.trigger()
        if trigger is None or position + CONTINUATION_BYTES > len(data):
            continue
        key = history.key(profile, trigger)
        prior = memory.get(key)
        continuation = data[position : position + CONTINUATION_BYTES]
        opportunities += 1
        if prior:
            wakes += 1
        try:
            receipt_id = prior.index(continuation)
        except ValueError:
            receipt_id = -1
        if receipt_id >= 0:
            output.extend((ESCAPE, COPY, receipt_id))
            copies += 1
            copied_bytes += CONTINUATION_BYTES
        else:
            for literal in continuation:
                _emit_literal(output, literal)
        history.observe(continuation)
        memory.add(key, continuation)
        position += CONTINUATION_BYTES
    return bytes(output), {
        "opportunities": opportunities,
        "wakes": wakes,
        "copies": copies,
        "copied_bytes": copied_bytes,
        "memory_keys": len(memory.rows),
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }


def _decode_ir(stream, size, profile):
    history = History()
    memory = ReceiptMemory()
    output = bytearray()
    position = 0
    while len(output) < size:
        byte, position = _read_literal(stream, position)
        output.append(byte)
        history.observe(bytes((byte,)))
        trigger = history.trigger()
        if trigger is None or len(output) + CONTINUATION_BYTES > size:
            continue
        key = history.key(profile, trigger)
        prior = memory.get(key)
        if (
            position + 2 < len(stream)
            and stream[position] == ESCAPE
            and stream[position + 1] == COPY
        ):
            receipt_id = stream[position + 2]
            position += 3
            if receipt_id >= len(prior):
                raise ValueError("receipt IR references unavailable continuation")
            continuation = prior[receipt_id]
        else:
            literal = bytearray()
            for _ in range(CONTINUATION_BYTES):
                value, position = _read_literal(stream, position)
                literal.append(value)
            continuation = bytes(literal)
        output.extend(continuation)
        history.observe(continuation)
        memory.add(key, continuation)
    if len(output) != size or position != len(stream):
        raise ValueError("receipt IR length mismatch")
    return bytes(output)


def compress(data):
    payloads = {"RAW": lzma.compress(data, preset=PRESET)}
    transform_stats = {}
    control_roundtrip = {"RAW": lzma.decompress(payloads["RAW"]) == data}
    for profile in ("C0", "E0"):
        stream, profile_stats = _encode_ir(data, profile)
        control_roundtrip[profile] = _decode_ir(stream, len(data), profile) == data
        if not control_roundtrip[profile]:
            raise RuntimeError(profile + " receipt IR failed roundtrip")
        payloads[profile] = lzma.compress(stream, preset=PRESET)
        transform_stats[profile] = profile_stats
    selected = min(MODES, key=lambda name: (len(payloads[name]), MODES.index(name)))
    mode = MODES.index(selected)
    _LAST_STATS.clear()
    _LAST_STATS.update(
        {
            "selected": selected,
            "payload_bytes": {name: len(payloads[name]) for name in MODES},
            "gain_vs_raw_lzma_bytes": {
                name: len(payloads["RAW"]) - len(payloads[name]) for name in MODES
            },
            "transform_stats": transform_stats,
            "control_roundtrip": control_roundtrip,
            "continuation_bytes": CONTINUATION_BYTES,
            "max_candidates": MAX_CANDIDATES,
            "max_keys": MAX_KEYS,
        }
    )
    return MAGIC + struct.pack(">IB", len(data), mode) + payloads[selected]


def decompress(archive):
    if len(archive) < 13 or archive[:8] != MAGIC:
        raise ValueError("invalid trigger receipt archive")
    size, mode = struct.unpack_from(">IB", archive, 8)
    if mode >= len(MODES):
        raise ValueError("invalid trigger receipt mode")
    stream = lzma.decompress(archive[13:])
    if mode == 0:
        if len(stream) != size:
            raise ValueError("raw trigger receipt length mismatch")
        return stream
    return _decode_ir(stream, size, MODES[mode])


def stats():
    return dict(_LAST_STATS)
