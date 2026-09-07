#!/usr/bin/env python3
"""Bounded categorical event coding with exact adaptive arithmetic replay.

The caller supplies the same pre-truth event schedule and reconstructed bytes
to each side. No serialized integer-byte model is involved. R and G share the
same predictor; X alone adds the supplied context to its specific-table key.
"""
from array import array
import hashlib
import struct
import sys


MODEL_SPEC = {
    "format": "gamma-dualstream-event-channel-v1",
    "arithmetic_bits": 32,
    "probability_denominator": 65536,
    "probability_minimum": 1,
    "probability_maximum": 65535,
    "tree": "balanced halves of [0,alphabet); floor midpoint; zero chooses lower half",
    "base_cells": 4096,
    "specific_cells": 65536,
    "base_initial_counts": [1, 1],
    "specific_initial_counts": [0, 0],
    "backoff_strength": 8,
    "backoff_probability": "floor((specific_one*65536+8*base_q16)/(specific_total+8)); clamp1..65535",
    "base_probability": "floor(base_one*65536/base_total); clamp1..65535",
    "update": "after each decoded bit, increment both matching counts; at total>=32768 ceil-half each count",
    "replacement": "direct mapped; new64-bit tag resets counts to the table's initial counts",
    "hash": "BLAKE2b64, little-endian words, explicit domains; zero tag maps to1",
    "base_key": ["kind", "alphabet", "binary_tree_prefix"],
    "specific_key": ["base_key", "two_previous_kind_value_hashes", "last_four_output_bytes", "output_history_length", "X_only_context"],
    "common_trace": "event schedule, contexts and categories, every count replacement/update, probabilities, decoded bits, common arithmetic state and emitted output",
    "decoder_lookahead": "decoder-only code register excluded from symmetric digest; common interval checked against encoder shadow after every bit",
    "cost_attribution": "whole arithmetic bytes charged to event category when emitted; final partial byte, four zero lookahead bytes and32-byte state digest charged to framing",
    "checksum": "SHA256 symmetric complete state digest appended after canonical arithmetic body",
    "max_events": 1000000,
    "max_binary_events": 20000000,
    "max_output_bytes": 1000000,
    "max_payload_bytes": 8000000,
    "max_alphabet": 1048576,
    "max_context_items": 16,
    "max_categories": 16,
}
MASK = (1 << 32) - 1
HALF = 1 << 31
QUARTER = 1 << 30
THREE_QUARTERS = 3 << 30


class EventCodecError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise EventCodecError(message)


def words(values):
    return struct.pack("<" + "Q" * len(values), *values)


def tag(data, domain):
    return int.from_bytes(hashlib.blake2b(data, digest_size=8, person=domain).digest(), "little") or 1


class _Writer:
    def __init__(self):
        self.data = bytearray()
        self.partial = self.used = 0

    def bit(self, value):
        self.partial = (self.partial << 1) | value
        self.used += 1
        if self.used == 8:
            require(len(self.data) < MODEL_SPEC["max_payload_bytes"] - 36, "payload budget")
            self.data.append(self.partial)
            self.partial = self.used = 0

    def finish(self):
        if self.used:
            self.data.append(self.partial << (8 - self.used))
            self.partial = self.used = 0
        # Explicitly transmitted lookahead, never an implicit infinite zero tail.
        self.data.extend(b"\0" * 4)
        return bytes(self.data)


class _Encoder:
    def __init__(self):
        self.low, self.high, self.pending = 0, MASK, 0
        self.writer = _Writer()

    def output(self, bit):
        self.writer.bit(bit)
        while self.pending:
            self.writer.bit(bit ^ 1)
            self.pending -= 1

    def put(self, bit, probability_one):
        split = self.low + ((self.high - self.low + 1) * (65536 - probability_one) // 65536) - 1
        if bit:
            self.low = split + 1
        else:
            self.high = split
        while True:
            if self.high < HALF:
                self.output(0)
            elif self.low >= HALF:
                self.output(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) | 1) & MASK

    def snapshot(self):
        return (self.low, self.high, self.pending, len(self.writer.data), self.writer.partial, self.writer.used)

    def finish(self):
        self.pending += 1
        self.output(0 if self.low < QUARTER else 1)
        return self.writer.finish()


class _Decoder:
    def __init__(self, body):
        self.body, self.position = body, 0
        self.low, self.high, self.code = 0, MASK, 0
        for _ in range(32):
            self.code = (self.code << 1) | self.read_bit()

    def read_bit(self):
        require(self.position < len(self.body) * 8, "truncated arithmetic lookahead")
        value = (self.body[self.position >> 3] >> (7 - (self.position & 7))) & 1
        self.position += 1
        return value

    def get(self, probability_one):
        split = self.low + ((self.high - self.low + 1) * (65536 - probability_one) // 65536) - 1
        bit = int(self.code > split)
        if bit:
            self.low = split + 1
        else:
            self.high = split
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF
                self.high -= HALF
                self.code -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.low -= QUARTER
                self.high -= QUARTER
                self.code -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) | 1) & MASK
            self.code = ((self.code << 1) | self.read_bit()) & MASK
        require(self.low <= self.code <= self.high, "arithmetic interval violation")
        return bit


class _Table:
    def __init__(self, cells, initial):
        self.tags = array("Q", [0]) * cells
        self.zero = array("H", [0]) * cells
        self.one = array("H", [0]) * cells
        self.mask, self.initial = cells - 1, initial

    def lookup(self, key):
        index = key & self.mask
        previous = (self.tags[index], self.zero[index], self.one[index])
        if self.tags[index] != key:
            self.tags[index] = key
            self.zero[index], self.one[index] = self.initial
        return index, previous

    def update(self, index, bit):
        if bit:
            self.one[index] += 1
        else:
            self.zero[index] += 1
        if self.zero[index] + self.one[index] >= 32768:
            self.zero[index] = (self.zero[index] + 1) // 2
            self.one[index] = (self.one[index] + 1) // 2

    def digest_into(self, digest):
        for values in (self.tags, self.zero, self.one):
            if sys.byteorder == "little":
                digest.update(values.tobytes())
            else:
                copied = array(values.typecode, values)
                copied.byteswap()
                digest.update(copied.tobytes())


class EventChannel:
    def __init__(self, mode, payload=None):
        require(mode in ("R", "G", "X"), "unknown event mode")
        require(payload is None or type(payload) is bytes, "payload must be exact bytes")
        self.mode, self.payload = mode, payload
        if payload is not None:
            require(37 <= len(payload) <= MODEL_SPEC["max_payload_bytes"], "payload size bound")
        self.encoder = _Encoder()
        self.decoder = None if payload is None else _Decoder(payload[:-32])
        self.base = _Table(4096, (1, 1))
        self.specific = _Table(65536, (0, 0))
        self.events = self.bits = self.output_bytes = 0
        self.previous = (0, 0)
        self.history = self.history_length = 0
        self.costs = {}
        self.closed = False
        self.probability_trace = hashlib.sha256(b"event-probabilities-v1")
        self.sync_trace = hashlib.sha256(b"event-synchronization-v1" + bytes([int(mode == "X")]))
        self.output_hash = hashlib.sha256()
        self._final_digest = None

    def _model_digest(self):
        result = hashlib.sha256(b"event-complete-model-state-v1")
        self.base.digest_into(result)
        self.specific.digest_into(result)
        result.update(words((int(self.mode == "X"), self.events, self.bits, self.output_bytes,
                             *self.previous, self.history, self.history_length)))
        result.update(self.output_hash.digest())
        return result.digest()

    def state_digest(self):
        if self._final_digest is not None:
            return self._final_digest
        result = hashlib.sha256(b"event-complete-common-state-v1" + self._model_digest())
        result.update(self.probability_trace.digest())
        result.update(self.sync_trace.digest())
        result.update(words(self.encoder.snapshot()))
        result.update(hashlib.sha256(self.encoder.writer.data).digest())
        return result.hexdigest()

    def _bit(self, kind, alphabet, prefix, context_bytes, value):
        require(self.bits < MODEL_SPEC["max_binary_events"], "binary event budget")
        base_key = struct.pack("<III", kind, alphabet, prefix)
        base_tag = tag(base_key, b"D2EventBaseV1")
        local_key = base_key + struct.pack("<QQIB", *self.previous, self.history, self.history_length) + context_bytes
        local_tag = tag(local_key, b"D2EventLocalV1")
        bi, before_base = self.base.lookup(base_tag)
        li, before_local = self.specific.lookup(local_tag)
        bz, bo = self.base.zero[bi], self.base.one[bi]
        lz, lo = self.specific.zero[li], self.specific.one[li]
        base_q = max(1, min(65535, bo * 65536 // (bz + bo)))
        probability = max(1, min(65535, (lo * 65536 + 8 * base_q) // (lz + lo + 8)))
        bit = value if self.decoder is None else self.decoder.get(probability)
        self.encoder.put(bit, probability)
        if self.decoder is not None:
            require((self.decoder.low, self.decoder.high) == (self.encoder.low, self.encoder.high),
                    "encoder/decoder interval divergence")
        self.base.update(bi, bit)
        self.specific.update(li, bit)
        self.probability_trace.update(struct.pack("<IHB", self.bits, probability, bit))
        mutation = (self.bits, kind, alphabet, prefix, probability, bit, bi, *before_base,
                    base_tag, bz, bo, self.base.zero[bi], self.base.one[bi],
                    li, *before_local, local_tag, lz, lo, self.specific.zero[li], self.specific.one[li],
                    *self.encoder.snapshot())
        self.sync_trace.update(b"B" + words(mutation))
        self.bits += 1
        return bit

    def event(self, kind, alphabet, value=None, context=(), category="program"):
        require(not self.closed, "closed event channel")
        require(type(kind) is int and 0 <= kind < (1 << 20), "event kind bound")
        require(type(alphabet) is int and 1 <= alphabet <= MODEL_SPEC["max_alphabet"], "event alphabet bound")
        require(type(context) is tuple and len(context) <= MODEL_SPEC["max_context_items"] and
                all(type(v) is int and -(1 << 63) <= v < (1 << 63) for v in context), "event context bound")
        require(type(category) is str and 1 <= len(category) <= 32 and category != "framing" and
                all(32 <= ord(c) < 127 for c in category), "event cost category")
        require(category in self.costs or len(self.costs) < MODEL_SPEC["max_categories"], "event category budget")
        require(self.events < MODEL_SPEC["max_events"], "categorical event budget")
        require((self.decoder is None and type(value) is int and 0 <= value < alphabet) or
                (self.decoder is not None and value is None), "event truth supplied on wrong side or out of range")
        packed_context = bytes([len(context)]) + b"".join(struct.pack("<q", c) for c in context)
        category_bytes = category.encode("ascii")
        self.sync_trace.update(b"E" + words((self.events, kind, alphabet)) + packed_context +
                               bytes([len(category_bytes)]) + category_bytes)
        key_context = packed_context if self.mode == "X" else b""
        start_bytes = len(self.encoder.writer.data)
        low, high, prefix = 0, alphabet, 1
        while high - low > 1:
            midpoint = (low + high) // 2
            bit = self._bit(kind, alphabet, prefix, key_context,
                            int(value >= midpoint) if self.decoder is None else None)
            if bit:
                low = midpoint
            else:
                high = midpoint
            prefix = prefix * 2 + bit
        decoded = low
        self.costs[category] = self.costs.get(category, 0) + len(self.encoder.writer.data) - start_bytes
        event_hash = tag(struct.pack("<II", kind, decoded), b"D2EventTruthV1")
        self.previous = (self.previous[1], event_hash)
        self.sync_trace.update(b"V" + words((decoded, *self.previous)))
        self.events += 1
        return decoded

    def emit(self, data):
        require(not self.closed, "closed event channel")
        require(isinstance(data, (bytes, bytearray, memoryview)), "output must be bytes")
        data = bytes(data)
        require(self.output_bytes + len(data) <= MODEL_SPEC["max_output_bytes"], "emitted output budget")
        if not data:
            return
        # Update every reconstructed byte, including dictionary/program copies.
        for value in data:
            self.history = ((self.history << 8) | value) & MASK
            self.history_length = min(4, self.history_length + 1)
            # Calls may group the same bytes differently on each side.
            self.sync_trace.update(b"O" + bytes([value]))
        self.output_bytes += len(data)
        self.output_hash.update(data)

    def finish(self):
        require(not self.closed, "closed event channel")
        body = self.encoder.finish()
        self.sync_trace.update(b"F" + words((len(body),)) + hashlib.sha256(body).digest())
        model_digest = self._model_digest().hex()
        self._final_digest = self.state_digest()
        encoded = body + bytes.fromhex(self._final_digest)
        require(len(encoded) <= MODEL_SPEC["max_payload_bytes"], "final payload budget")
        if self.payload is not None:
            require(encoded == self.payload, "noncanonical, truncated, trailing or corrupt event stream")
        self.closed = True
        costs = dict(sorted(self.costs.items()))
        costs["framing"] = len(encoded) - sum(costs.values())
        require(all(v >= 0 for v in costs.values()) and sum(costs.values()) == len(encoded), "event cost accounting")
        report = dict(mode=self.mode, events=self.events, binary_events=self.bits, emitted_bytes=self.output_bytes,
                      payload_bytes=len(encoded), arithmetic_body_bytes=len(body), termination_lookahead_bytes=4,
                      state_checksum_bytes=32, actual_bytes_by_category=costs,
                      attribution="category at byte emission; delayed and terminal bytes in framing",
                      output_sha256=self.output_hash.hexdigest(), model_state_digest=model_digest,
                      probability_trace_sha256=self.probability_trace.hexdigest(),
                      sync_trace_sha256=self.sync_trace.hexdigest(), state_digest=self._final_digest,
                      common_coder_state=list(self.encoder.snapshot()),
                      canonical_reencode_pass=True)
        return (encoded if self.payload is None else None), report
