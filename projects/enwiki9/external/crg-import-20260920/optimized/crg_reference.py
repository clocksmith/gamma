#!/usr/bin/env python3
"""CRG reference, CRG2 format version 2: real byte archives, causal memories, and measured controls.

Standard library only; Python 3.10+. This is a research codec, NOT a Hutter
Prize winner. No function declares prize eligibility from estimated bit counts.
The generic reference predictor is not FX2, CMIX, or an implementation thereof.

Format CRG2: fixed 96-byte header, followed by exactly the declared payload.
The header contains mode, format version, original length, exact payload bit
length, payload byte length, original SHA-256, and payload SHA-256. For CRG
payloads a 32-bit binary arithmetic coder uses nonzero Q16 probabilities and
explicit termination/padding. No external vocabulary or labels are needed.
All contextual decisions are derived from previously reconstructed raw bytes.

Relations are depth-one exact ASCII word copies, not a general recursive grammar.
The bounded parser recognizes title/text/page tags and wiki link-target starts.
It is an optional predictor, not an XML validator or a byte transformation.
Malformed markup is still encoded exactly. Donors become eligible only after
completion. Shared donor weights persist while the selected donor set is stable.
The outer parent/expert posterior persists across the entire file.

Fixed-point posterior rounding changes ideal Bayesian guarantees: this program
claims exact reproducibility of its specified integer algorithm, NOT a universal
one-bit finite-archive bound. Modes 7..10 identify order-6 backoff with shrinkage 4, selected on development data; old modes remain unchanged.
Format changes require a new version.

Copyright (c) 2026. MIT License. Provided without warranty.
"""
from __future__ import annotations

import argparse
from array import array
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import zlib
import lzma

Q = 1 << 16
POST = 1 << 40
MASK = (1 << 32) - 1
HALF = 1 << 31
QUARTER = 1 << 30
THREE_QUARTERS = 3 << 30
MAGIC = b"CRG2"
VERSION = 2
HEADER = struct.Struct(">4sBBHQQQ32s32s")
assert HEADER.size == 96
ARMS = ("parent", "bookkeeping", "independent", "shared", "wrong")
ARM_ID = {"parent": 0, "bookkeeping": 0, "independent": 1,
          "shared": 2, "wrong": 3}
ID_ARM = {0: "parent", 1: "independent", 2: "shared", 3: "wrong",
          7: "parent", 8: "independent", 9: "shared", 10: "wrong"}
BACKEND_ID = {"deflate": 4, "lzma": 5, "stored": 6}
BUFFER = 65536
CONTEXT_SLOTS = 1 << 16
WORD_CAPACITY = 32
WORD_LIMIT = 64
DONOR_SLOTS = 4
HIGH_SLOTS = 1 << 18
TAG_LIMIT = 512


class FormatError(ValueError):
    """The archive is malformed, corrupt, or exceeds an explicit bound."""


def clamp_count(n: int) -> int:
    return max(1, min(Q - 1, n))


def posterior_update(weights: list[int], emissions: list[int], bit: int) -> None:
    """Largest remainder with one quantum per state and stable-index ties."""
    if not weights or all(p == emissions[0] for p in emissions):
        return
    products = [w * (p if bit else Q - p)
                for w, p in zip(weights, emissions)]
    total = sum(products)
    available = POST - len(weights)
    divisions = [divmod(v * available, total) for v in products]
    updated = [1 + a for a, _ in divisions]
    left = POST - sum(updated)
    ranking = sorted(range(len(weights)), key=lambda i: (-divisions[i][1], i))
    for i in ranking[:left]:
        updated[i] += 1
    weights[:] = updated


def uniform_weights(n: int) -> list[int]:
    if not n:
        return []
    a, b = divmod(POST, n)
    return [a + (i < b) for i in range(n)]


def marginal(weights: list[int], probabilities: list[int]) -> int:
    return clamp_count((sum(w * p for w, p in zip(weights, probabilities))
                        + POST // 2) // POST)


class BitWriter:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = bytearray()
        self.current = 0
        self.used = 0
        self.bits = 0
        self.bytes = 0
        self.digest = hashlib.sha256()

    def put(self, bit: int) -> None:
        self.current = (self.current << 1) | bit
        self.used += 1
        self.bits += 1
        if self.used == 8:
            self.buffer.append(self.current)
            self.current = self.used = 0
            if len(self.buffer) >= BUFFER:
                self.flush()

    def flush(self) -> None:
        if self.buffer:
            self.stream.write(self.buffer)
            self.digest.update(self.buffer)
            self.bytes += len(self.buffer)
            self.buffer.clear()

    def finish(self) -> None:
        if self.used:
            self.buffer.append(self.current << (8 - self.used))
        self.current = self.used = 0
        self.flush()


class BitReader:
    def __init__(self, stream, bits: int):
        self.stream = stream
        self.limit = bits
        self.read_bits = 0
        self.buffer = b""
        self.index = 0
        self.byte = 0
        self.left = 0

    def get(self) -> int:
        if self.read_bits >= self.limit:
            raise FormatError("arithmetic payload exhausted")
        if not self.left:
            if self.index == len(self.buffer):
                self.buffer = self.stream.read(BUFFER)
                self.index = 0
                if not self.buffer:
                    raise FormatError("truncated arithmetic payload")
            self.byte = self.buffer[self.index]
            self.index += 1
            self.left = 8
        self.left -= 1
        self.read_bits += 1
        return (self.byte >> self.left) & 1


class ArithmeticEncoder:
    def __init__(self, writer: BitWriter):
        self.writer = writer
        self.low = 0
        self.high = MASK
        self.pending = 0

    def emit(self, bit: int) -> None:
        self.writer.put(bit)
        for _ in range(self.pending):
            self.writer.put(1 - bit)
        self.pending = 0

    def put(self, bit: int, p1: int) -> None:
        split = self.low + ((self.high - self.low + 1) * (Q - p1) // Q)
        if bit:
            self.low = split
        else:
            self.high = split - 1
        while True:
            if self.high < HALF:
                self.emit(0)
            elif self.low >= HALF:
                self.emit(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self) -> None:
        self.pending += 1
        self.emit(0 if self.low < QUARTER else 1)
        # Stored, counted padding. Decoder never fabricates zeros on EOF.
        for _ in range(32):
            self.writer.put(0)
        self.writer.finish()


class ArithmeticDecoder:
    def __init__(self, reader: BitReader):
        self.reader = reader
        self.low = 0
        self.high = MASK
        self.code = 0
        for _ in range(32):
            self.code = (self.code << 1) | reader.get()

    def get(self, p1: int) -> int:
        split = self.low + ((self.high - self.low + 1) * (Q - p1) // Q)
        bit = int(self.code >= split)
        if bit:
            self.low = split
        else:
            self.high = split - 1
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
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self.reader.get()
        return bit


class ContextPredictor:
    """Bounded order-0/1/hashed-order-2 binary context backoff. No learned assets."""
    def __init__(self):
        self.c0 = array("H", [0]) * 512
        self.c1 = array("H", [0]) * (257 * 256 * 2)
        self.c2 = array("H", [0]) * (CONTEXT_SLOTS * 2)
        self.tags = array("I", [0]) * CONTEXT_SLOTS
        self.previous = 256
        self.last_two = 0
        self.nbytes = 0
        self.i0 = self.i1 = self.i2 = self.key = 0

    def predict(self, prefix: int) -> int:
        self.i0 = prefix * 2
        self.i1 = ((self.previous << 8) | prefix) * 2
        n0, o0 = self.c0[self.i0], self.c0[self.i0 + 1]
        p = (Q * (o0 + 1)) // (n0 + o0 + 2)
        n1, o1 = self.c1[self.i1], self.c1[self.i1 + 1]
        p = (Q * o1 + 8 * p) // (n1 + o1 + 8)
        self.key = ((self.last_two << 8) | prefix) + 1
        self.i2 = (((self.key ^ (self.key >> 11)) * 2654435761)
                   & (CONTEXT_SLOTS - 1)) * 2
        if self.nbytes >= 2 and self.tags[self.i2 // 2] == self.key:
            n2, o2 = self.c2[self.i2], self.c2[self.i2 + 1]
            p = (Q * o2 + 12 * p) // (n2 + o2 + 12)
        return clamp_count(p)

    @staticmethod
    def increment(counts, index: int, bit: int) -> None:
        counts[index + bit] += 1
        if counts[index] + counts[index + 1] >= 512:
            counts[index] = (counts[index] + 1) // 2
            counts[index + 1] = (counts[index + 1] + 1) // 2

    def observe(self, bit: int) -> None:
        self.increment(self.c0, self.i0, bit)
        self.increment(self.c1, self.i1, bit)
        if self.nbytes >= 2:
            if self.tags[self.i2 // 2] != self.key:
                self.tags[self.i2 // 2] = self.key
                self.c2[self.i2] = self.c2[self.i2 + 1] = 0
            self.increment(self.c2, self.i2, bit)

    def end_byte(self, byte: int) -> None:
        self.previous = byte
        self.last_two = ((self.last_two << 8) | byte) & 65535
        self.nbytes += 1

    def digest(self) -> str:
        h = hashlib.sha256()
        for a in (self.c0, self.c1, self.c2, self.tags):
            # Canonical little-endian state witness independent of host endian.
            b = array(a.typecode, a)
            if sys.byteorder != "little":
                b.byteswap()
            h.update(b.tobytes())
        h.update(struct.pack(">QQQ", self.previous, self.last_two, self.nbytes))
        return h.hexdigest()


class HighContextPredictor:
    """Separate enhanced profile: bounded exact-tag suffix contexts, orders 2..6.

    Context collisions evict state deterministically; tags prevent treating a
    colliding key as an observed context. This is conventional backoff modeling,
    not a claimed novel algorithm or a competitive FX2 implementation.
    """
    def __init__(self):
        self.c0 = array("H", [0]) * 512
        self.c1 = array("H", [0]) * (257 * 256 * 2)
        self.counts = [array("H", [0]) * (HIGH_SLOTS * 2) for _ in range(5)]
        self.tags = [array("Q", [0]) * HIGH_SLOTS for _ in range(5)]
        self.indices = [0] * 5
        self.keys = [0] * 5
        self.previous = 256
        self.history = self.nbytes = self.i0 = self.i1 = 0

    @staticmethod
    def hash(x):
        x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & ((1 << 64) - 1)
        x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & ((1 << 64) - 1)
        return x ^ (x >> 31)

    def predict(self, prefix):
        self.i0 = prefix * 2
        self.i1 = ((self.previous << 8) | prefix) * 2
        p = Q * (self.c0[self.i0 + 1] + 1) // (self.c0[self.i0] + self.c0[self.i0 + 1] + 2)
        p = (Q * self.c1[self.i1 + 1] + 8 * p) // (self.c1[self.i1] + self.c1[self.i1 + 1] + 8)
        for j in range(5):
            order = j + 2
            key = (((self.history & ((1 << (8 * order)) - 1)) << 8) | prefix) + 1
            i = (self.hash(key) & (HIGH_SLOTS - 1)) * 2
            self.keys[j], self.indices[j] = key, i
            if self.nbytes >= order and self.tags[j][i // 2] == key:
                c = self.counts[j]
                p = (Q * c[i + 1] + 4 * p) // (c[i] + c[i + 1] + 4)
        return clamp_count(p)

    def observe(self, bit):
        ContextPredictor.increment(self.c0, self.i0, bit)
        ContextPredictor.increment(self.c1, self.i1, bit)
        for j in range(5):
            if self.nbytes < j + 2:
                continue
            c, i = self.counts[j], self.indices[j]
            if self.tags[j][i // 2] != self.keys[j]:
                self.tags[j][i // 2] = self.keys[j]
                c[i] = c[i + 1] = 0
            ContextPredictor.increment(c, i, bit)

    def end_byte(self, byte):
        self.previous = byte
        self.history = ((self.history << 8) | byte) & ((1 << 48) - 1)
        self.nbytes += 1

    def digest(self):
        h = hashlib.sha256()
        for a in (self.c0, self.c1, *self.counts, *self.tags):
            b = array(a.typecode, a)
            if sys.byteorder != "little":
                b.byteswap()
            h.update(b.tobytes())
        h.update(struct.pack(">QQQ", self.previous, self.history, self.nbytes))
        return h.hexdigest()


def is_letter(byte: int) -> bool:
    return 65 <= byte <= 90 or 97 <= byte <= 122


def remember(pool: deque, word: bytes) -> None:
    if word in pool:
        pool.remove(word)
    pool.append(word)


class DualHistoryParser:
    """Bounded, conservative causal feature parser. Never alters any input byte."""
    def __init__(self):
        self.title = deque(maxlen=WORD_CAPACITY)
        self.body = deque(maxlen=WORD_CAPACITY)
        self.pending_title = deque(maxlen=WORD_CAPACITY)
        self.field = 0  # 0 other, 1 title, 2 text
        self.in_tag = False
        self.tag = bytearray()
        self.quote = 0
        self.tag_overflow = False
        self.word = bytearray()
        self.inside_word = False
        self.word_overflow = False
        self.link = False
        self.previous = 0

    def finish_word(self) -> None:
        if not self.word_overflow and 3 <= len(self.word) <= WORD_LIMIT:
            if self.field == 1:
                remember(self.pending_title, bytes(self.word))
            elif self.field == 2:
                remember(self.body, bytes(self.word))
        self.word.clear()
        self.word_overflow = False
        self.inside_word = False

    def finish_tag(self) -> None:
        if not self.tag_overflow:
            s = bytes(self.tag).strip()
            closing = s.startswith(b"/")
            if closing:
                s = s[1:].lstrip()
            name = s.split(None, 1)[0].rstrip(b"/") if s else b""
            self_closing = s.rstrip().endswith(b"/")
            if name == b"page":
                self.title.clear(); self.body.clear(); self.pending_title.clear()
                self.field = 0; self.link = False
            elif name == b"title":
                if closing:
                    self.title = deque(self.pending_title, maxlen=WORD_CAPACITY)
                    self.pending_title.clear(); self.field = 0
                elif not self_closing:
                    self.pending_title.clear(); self.field = 1
            elif name == b"text":
                self.field = 0 if closing or self_closing else 2
                self.link = False
        self.in_tag = False
        self.tag.clear(); self.tag_overflow = False; self.quote = 0

    def observe(self, byte: int) -> None:
        if self.in_tag:
            if byte == 62 and not self.quote:
                self.finish_tag()
            else:
                if self.quote:
                    if byte == self.quote:
                        self.quote = 0
                elif byte in (34, 39):
                    self.quote = byte
                if len(self.tag) < TAG_LIMIT:
                    self.tag.append(byte)
                else:
                    self.tag_overflow = True
            self.previous = byte
            return
        if byte == 60:
            self.finish_word()
            self.in_tag = True
            self.tag.clear(); self.quote = 0; self.tag_overflow = False
        else:
            if self.field in (1, 2) and is_letter(byte):
                self.inside_word = True
                if len(self.word) < WORD_LIMIT:
                    self.word.append(byte)
                else:
                    self.word_overflow = True
            else:
                self.finish_word()
            if self.field == 2:
                if byte == 91 and self.previous == 91:
                    self.link = True
                elif byte in (124, 93):
                    self.link = False
        self.previous = byte

    def role(self):
        return (1 if self.link else 0) if self.field == 2 and not self.in_tag else None

    def snapshot(self):
        return {"title": [x.hex() for x in self.title],
                "body": [x.hex() for x in self.body],
                "pending_title": [x.hex() for x in self.pending_title],
                "field": self.field, "in_tag": self.in_tag, "tag": self.tag.hex(),
                "quote": self.quote, "tag_overflow": self.tag_overflow,
                "word": self.word.hex(), "inside_word": self.inside_word,
                "word_overflow": self.word_overflow, "link": self.link,
                "previous": self.previous}


def wrong_spelling(word: bytes) -> bytes:
    # Transforms actual emissions, not merely latent-state labels. All donor
    # letters change, with identical lengths/capacity and no future access.
    return bytes((65 + (b - 65 + 13) % 26) if b <= 90
                 else (97 + (b - 97 + 13) % 26) for b in word)


class Binding:
    def __init__(self):
        self.donors = ()
        self.weights = []
        self.active = []
        self.position = 0
        self.probabilities = []

    def start(self, donors: tuple[bytes, ...], independent: bool) -> None:
        if donors != self.donors or independent:
            self.weights = uniform_weights(len(donors))
        self.donors = donors
        self.active = [True] * len(donors)
        self.position = 0

    def predict(self, parent: int, depth: int, wrong: bool) -> int:
        self.probabilities = []
        for donor, active in zip(self.donors, self.active):
            p = parent
            if active and self.position < len(donor):
                value = donor[self.position]
                if wrong:
                    value = wrong_spelling(bytes((value,)))[0]
                bit = (value >> (7 - depth)) & 1
                p = (parent + (Q - 1 if bit else 1) + 1) // 2
            self.probabilities.append(p)
        return marginal(self.weights, self.probabilities) if self.weights else parent

    def observe(self, bit: int, depth: int, wrong: bool) -> None:
        posterior_update(self.weights, self.probabilities, bit)
        for i, donor in enumerate(self.donors):
            if not self.active[i]:
                continue
            value = donor[self.position]
            if wrong:
                value = wrong_spelling(bytes((value,)))[0]
            if ((value >> (7 - depth)) & 1) != bit:
                self.active[i] = False
        if depth == 7:
            self.position += 1
            for i, donor in enumerate(self.donors):
                if self.position >= len(donor):
                    self.active[i] = False

    def snapshot(self):
        return {"donors": [d.hex() for d in self.donors], "weights": self.weights,
                "active": self.active, "position": self.position,
                "probabilities": self.probabilities}


class RelationalTransducer:
    def __init__(self, arm: str):
        self.arm = arm
        self.parser = DualHistoryParser()
        self.banks = [Binding(), Binding()]
        self.outer = uniform_weights(2)
        self.current_role = None
        self.parent = self.relational = Q // 2
        self.depth = 0
        self.active_bits = 0
        self.mentions = 0

    def begin_byte(self) -> None:
        self.current_role = self.parser.role()
        if self.current_role is not None and not self.parser.inside_word:
            pool = self.parser.title if self.current_role == 0 else self.parser.body
            donors = tuple(list(pool)[-DONOR_SLOTS:])
            self.banks[self.current_role].start(donors, self.arm == "independent")
            self.mentions += 1

    def predict(self, parent: int, depth: int) -> int:
        self.parent = self.relational = parent
        self.depth = depth
        if self.current_role is not None:
            bank = self.banks[self.current_role]
            self.relational = bank.predict(parent, depth, self.arm == "wrong")
            self.active_bits += int(any(bank.active))
        return marginal(self.outer, [parent, self.relational])

    def observe_bit(self, bit: int) -> None:
        posterior_update(self.outer, [self.parent, self.relational], bit)
        if self.current_role is not None:
            self.banks[self.current_role].observe(bit, self.depth, self.arm == "wrong")

    def end_byte(self, byte: int) -> None:
        self.parser.observe(byte)

    def digest(self) -> str:
        # Arm omitted: K and shared execute identical introduced state.
        obj = {"parser": self.parser.snapshot(), "banks": [b.snapshot() for b in self.banks],
               "outer": self.outer, "role": self.current_role,
               "parent": self.parent, "relational": self.relational,
               "depth": self.depth, "active_bits": self.active_bits, "mentions": self.mentions}
        return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Engine:
    def __init__(self, arm: str, witness: bool, profile: int = 0):
        self.arm = arm
        self.parent = HighContextPredictor() if profile else ContextPredictor()
        self.relation = None if arm == "parent" else RelationalTransducer(arm)
        self.witness = hashlib.sha256() if witness else None
        self.trace = bytearray()

    def process(self, coder, byte=None) -> int:
        if self.relation:
            self.relation.begin_byte()
        prefix = 1
        out = 0
        for depth in range(8):
            p = self.parent.predict(prefix)
            q = p
            if self.relation:
                candidate = self.relation.predict(p, depth)
                if self.arm != "bookkeeping":
                    q = candidate
            if byte is None:
                bit = coder.get(q)
            else:
                bit = (byte >> (7 - depth)) & 1
                coder.put(bit, q)
            if self.witness is not None:
                self.trace.extend((q >> 8, q & 255, bit))
            self.parent.observe(bit)
            if self.relation:
                self.relation.observe_bit(bit)
            prefix = (prefix << 1) | bit
            out = (out << 1) | bit
        self.parent.end_byte(out)
        if self.relation:
            self.relation.end_byte(out)
        if len(self.trace) >= BUFFER:
            self.witness.update(self.trace)
            self.trace.clear()
        return out

    def report(self):
        if self.witness is not None:
            self.witness.update(self.trace); self.trace.clear()
        return {"parent_state_sha256": self.parent.digest(),
                "relation_state_sha256": self.relation.digest() if self.relation else None,
                "prediction_sha256": self.witness.hexdigest() if self.witness is not None else None,
                "active_bits": self.relation.active_bits if self.relation else 0,
                "mentions": self.relation.mentions if self.relation else 0}


def deadline_check(start: float, limit: float | None) -> None:
    if limit is not None and time.monotonic() - start > limit:
        raise TimeoutError("operation exceeded the requested time limit")


def temporary_destination(source: Path, target: Path, force: bool):
    if source.resolve() == target.resolve():
        raise ValueError("input and output must be different files")
    if target.exists() and not force:
        raise FileExistsError(str(target))
    fd, name = tempfile.mkstemp(prefix="." + target.name + ".", suffix=".partial", dir=target.parent)
    return fd, Path(name)


def commit_output(temp: Path, target: Path, force: bool) -> None:
    if force:
        os.replace(temp, target)
    else:
        os.link(temp, target)  # Atomic no-overwrite publication on one filesystem.
        temp.unlink()


def compress(source, target, *, arm="shared", backend="crg", force=False,
             witness=False, time_limit=None, profile=0):
    source, target = Path(source), Path(target)
    if arm not in ARMS or backend not in ("crg", *BACKEND_ID):
        raise ValueError("unknown arm/backend")
    if profile not in (0, 1):
        raise ValueError("unknown context profile")
    mode = ARM_ID[arm] + (7 if profile else 0) if backend == "crg" else BACKEND_ID[backend]
    start = time.monotonic()
    fd, temp = temporary_destination(source, target, force)
    original = hashlib.sha256()
    n = 0
    detail = {}
    try:
        with source.open("rb") as inp, os.fdopen(fd, "w+b") as out:
            out.write(b"\0" * HEADER.size)
            if backend == "crg":
                writer = BitWriter(out); coder = ArithmeticEncoder(writer); model = Engine(arm, witness, profile)
                while chunk := inp.read(BUFFER):
                    original.update(chunk)
                    for b in chunk:
                        model.process(coder, b); n += 1
                        if n % 1024 == 0:
                            deadline_check(start, time_limit)
                coder.finish()
                payload_n, bits, payload_hash = writer.bytes, writer.bits, writer.digest.digest()
                detail = model.report()
            else:
                compressor = zlib.compressobj(9) if backend == "deflate" else (
                    lzma.LZMACompressor(preset=6) if backend == "lzma" else None)
                hasher = hashlib.sha256(); payload_n = 0
                while chunk := inp.read(BUFFER):
                    original.update(chunk); n += len(chunk)
                    coded = compressor.compress(chunk) if compressor else chunk
                    out.write(coded); hasher.update(coded); payload_n += len(coded)
                    deadline_check(start, time_limit)
                tail = compressor.flush() if compressor else b""
                out.write(tail); hasher.update(tail); payload_n += len(tail)
                bits, payload_hash = payload_n * 8, hasher.digest()
            out.seek(0)
            out.write(HEADER.pack(MAGIC, VERSION, mode, 0, n, bits, payload_n,
                                  original.digest(), payload_hash))
            out.flush(); os.fsync(out.fileno())
        commit_output(temp, target, force)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return {"operation": "encode", "backend": backend, "arm": arm if backend == "crg" else None,
            "raw_bytes": n, "archive_bytes": HEADER.size + payload_n,
            "payload_bytes": payload_n, "framing_bytes": HEADER.size,
            "raw_sha256": original.hexdigest(), "payload_sha256": payload_hash.hex(),
            "elapsed_seconds": time.monotonic() - start,
            "hutter_qualified": False, **detail}


def read_header(inp, maximum: int):
    raw = inp.read(HEADER.size)
    if len(raw) != HEADER.size:
        raise FormatError("truncated header")
    magic, version, mode, flags, n, bits, payload_n, sha, psha = HEADER.unpack(raw)
    if magic != MAGIC or version != VERSION or flags or mode not in range(11):
        raise FormatError("unsupported archive format")
    if n > maximum:
        raise FormatError("declared output exceeds --max-output")
    if payload_n != (bits + 7) // 8 or (mode in ID_ARM and bits < 34):
        raise FormatError("invalid payload length")
    if mode in BACKEND_ID.values() and bits != payload_n * 8:
        raise FormatError("invalid byte-backend bit length")
    if os.fstat(inp.fileno()).st_size != HEADER.size + payload_n:
        raise FormatError("truncated payload or trailing archive bytes")
    digest = hashlib.sha256(); remaining = payload_n; last = 0
    while remaining:
        data = inp.read(min(BUFFER, remaining))
        if not data:
            raise FormatError("truncated payload")
        digest.update(data); remaining -= len(data); last = data[-1]
    if digest.digest() != psha:
        raise FormatError("payload checksum mismatch")
    if bits % 8 and last & ((1 << (8 - bits % 8)) - 1):
        raise FormatError("nonzero padding")
    inp.seek(HEADER.size)
    return mode, n, bits, payload_n, sha


def decompress(source, target, *, force=False, witness=False, max_output=1000000000,
               time_limit=None, bookkeeping=False):
    source, target = Path(source), Path(target)
    start = time.monotonic(); detail = {}; digest = hashlib.sha256(); nout = 0
    with source.open("rb") as inp:
        mode, n, bits, payload_n, sha = read_header(inp, max_output)
        fd, temp = temporary_destination(source, target, force)
        try:
            with os.fdopen(fd, "wb") as out:
                if mode in ID_ARM:
                    arm = "bookkeeping" if mode in (0, 7) and bookkeeping else ID_ARM[mode]
                    model = Engine(arm, witness, int(mode >= 7)); coder = ArithmeticDecoder(BitReader(inp, bits))
                    buffer = bytearray()
                    for i in range(n):
                        buffer.append(model.process(coder))
                        if len(buffer) >= BUFFER:
                            out.write(buffer); digest.update(buffer); nout += len(buffer); buffer.clear()
                        if i % 1024 == 0:
                            deadline_check(start, time_limit)
                    out.write(buffer); digest.update(buffer); nout += len(buffer)
                    detail = model.report()
                else:
                    dec = zlib.decompressobj() if mode == 4 else (
                        lzma.LZMADecompressor(memlimit=1 << 28) if mode == 5 else None)
                    remaining = payload_n
                    while remaining:
                        data = inp.read(min(BUFFER, remaining)); remaining -= len(data)
                        if dec is None:
                            blocks = [data]
                            for block in blocks:
                                nout += len(block)
                                if nout > n:
                                    raise FormatError("output length exceeded")
                                out.write(block); digest.update(block)
                        else:
                            while True:
                                limit = min(BUFFER, n - nout + 1)
                                block = dec.decompress(data, max_length=limit)
                                nout += len(block)
                                if nout > n:
                                    raise FormatError("output length exceeded")
                                out.write(block); digest.update(block)
                                deadline_check(start, time_limit)
                                if dec.eof:
                                    if dec.unused_data or remaining:
                                        raise FormatError("trailing compressed stream")
                                    break
                                if mode == 4:
                                    data = dec.unconsumed_tail
                                    if not data:
                                        break
                                else:
                                    if dec.needs_input:
                                        break
                                    data = b""
                        deadline_check(start, time_limit)
                    if dec is not None and not dec.eof:
                        raise FormatError("unfinished compressed stream")
                if nout != n or digest.digest() != sha:
                    raise FormatError("restored length/hash mismatch")
                out.flush(); os.fsync(out.fileno())
            commit_output(temp, target, force)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    return {"operation": "decode", "raw_bytes": nout, "raw_sha256": digest.hexdigest(),
            "archive_bytes": HEADER.size + payload_n,
            "elapsed_seconds": time.monotonic() - start, "hutter_qualified": False, **detail}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compress"); c.add_argument("input", type=Path); c.add_argument("output", type=Path)
    c.add_argument("--arm", choices=ARMS, default="shared")
    c.add_argument("--profile", choices=(0, 1), type=int, default=0)
    c.add_argument("--backend", choices=("crg", "deflate", "lzma", "stored"), default="crg")
    d = sub.add_parser("decompress"); d.add_argument("input", type=Path); d.add_argument("output", type=Path)
    d.add_argument("--max-output", type=int, default=1000000000)
    d.add_argument("--bookkeeping", action="store_true", help="replay K bookkeeping on a P/K archive")
    for p in (c, d):
        p.add_argument("--force", action="store_true")
        p.add_argument("--witness", action="store_true", help="hash every actual probability and decoded bit")
        p.add_argument("--time-limit", type=float)
    args = parser.parse_args(argv)
    if args.time_limit is not None and args.time_limit <= 0:
        parser.error("--time-limit must be positive")
    try:
        if args.command == "compress":
            result = compress(args.input, args.output, arm=args.arm, backend=args.backend,
                              force=args.force, witness=args.witness, time_limit=args.time_limit, profile=args.profile)
        else:
            if args.max_output < 0:
                parser.error("--max-output must be nonnegative")
            result = decompress(args.input, args.output, force=args.force, witness=args.witness,
                                time_limit=args.time_limit, max_output=args.max_output,
                                bookkeeping=args.bookkeeping)
    except (OSError, ValueError, TimeoutError, EOFError, lzma.LZMAError, zlib.error) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
