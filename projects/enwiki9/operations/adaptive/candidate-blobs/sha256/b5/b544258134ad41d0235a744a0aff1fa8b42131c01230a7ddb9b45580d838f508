#!/usr/bin/env python3
"""Bounded causal word coding over the unchanged opcode/BZip2 parent.

P/K retain OWB1 archives byte-for-byte. OWF1t and OWF1l have equally sized
five-byte headers and one BZip2 member. Only T emits FIFO slot references;
L escapes literals and learns the same dictionary without using references.
The decoder learns exclusively from bytes it has reconstructed. No corpus,
trained model, grammar discovery or transmitted word table is needed to decode.
"""
from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import struct
import sys
import tempfile
import time
from types import ModuleType
from typing import TYPE_CHECKING

# This static import declares the dependency for the existing source-closure
# scanner. Execution below compiles the exact hash-checked source bytes.
if TYPE_CHECKING:
    from programs.opcode_word_bz2_v1 import program as parent_dependency

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATH = ROOT / "programs/opcode_word_bz2_v1/program.py"
PARENT_SHA256 = "105af140b519896047cafbc41827e073100782ff1b212573279fa38a39c8c6d0"
MAX_RAW = 250_000
MAX_ARCHIVE = 8_000_000
MAX_OPCODE = 2 * MAX_RAW
MAX_PACKED = 4 * MAX_RAW + 1 + 64 * 33
SLOTS = 128
ARMS = ("P", "K", "T", "L")
TOKENS = re.compile(rb"[A-Za-z]+|[^A-Za-z]+")
LAST_REPORT = {}


class CodecError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CodecError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parent_module():
    source = PARENT_PATH.read_bytes()
    require(sha(source) == PARENT_SHA256, "parent source identity differs")
    module = ModuleType("causal_wordcode_bound_parent")
    exec(compile(source, str(PARENT_PATH), "exec"), module.__dict__)
    return module


def alpha(byte):
    return 65 <= byte <= 90 or 97 <= byte <= 122


class Lexicon:
    """FIFO insertion slots: an existing word never changes replacement order."""
    def __init__(self):
        self.slots = [None] * SLOTS
        self.ids = {}
        self.next_slot = 0
        self.words = self.bytes_seen = self.insertions = self.evictions = 0
        self.transitions = hashlib.sha256(b"causal-wordcode-fifo128-transitions-v1\0")

    def observe_word(self, word, end_offset):
        self.words += 1
        inserted = -1
        if 5 <= len(word) <= 32 and word not in self.ids:
            inserted = self.next_slot
            previous = self.slots[inserted]
            if previous is not None:
                del self.ids[previous]
                self.evictions += 1
            self.slots[inserted] = word
            self.ids[word] = inserted
            self.next_slot = (inserted + 1) % SLOTS
            self.insertions += 1
        self.transitions.update(struct.pack("<IIhI", self.words, end_offset, inserted, len(word)))
        self.transitions.update(word)

    def serialize(self):
        data = bytearray(b"FIFO128v1\0" + bytes([self.next_slot]))
        data.extend(struct.pack("<IIII", self.words, self.bytes_seen, self.insertions, self.evictions))
        for word in self.slots:
            data.append(len(word) if word is not None else 0)
            if word is not None:
                data.extend(word)
        return bytes(data)

    def report(self):
        return dict(state_digest=sha(self.serialize()), transition_digest=self.transitions.hexdigest(),
                    word_events=self.words, occupied_slots=len(self.ids), next_slot=self.next_slot,
                    insertions=self.insertions, evictions=self.evictions,
                    opcode_bytes=self.bytes_seen, serialized_state_bytes=len(self.serialize()))


def append_bounded(output, value, limit, label):
    require(len(value) <= limit - len(output), label + " output bound exceeded")
    output.extend(value)


def pack_words(data, references=True):
    require(len(data) <= MAX_OPCODE, "opcode input bound exceeded")
    lexicon, output, references_used = Lexicon(), bytearray(), 0
    for match in TOKENS.finditer(data):
        token = match.group()
        if alpha(token[0]):
            slot = lexicon.ids.get(token)
            if references and slot is not None:
                output.extend((1, slot + 1))
                references_used += 1
            else:
                output.extend(token)
            lexicon.observe_word(token, match.end())
        else:
            output.extend(token.replace(b"\x01", b"\x01\0"))
    require(len(output) <= MAX_PACKED, "packed output bound exceeded")
    lexicon.bytes_seen = len(data)
    return bytes(output), {**lexicon.report(), "references": references_used}


def unpack_words(data, references=True):
    require(len(data) <= MAX_PACKED, "packed input bound exceeded")
    lexicon, output, index, previous_word, count = Lexicon(), bytearray(), 0, False, 0
    while index < len(data):
        byte = data[index]
        if byte == 1:
            require(index + 1 < len(data), "truncated word escape")
            code = data[index + 1]
            index += 2
            if code:
                require(references, "reference forbidden in literal arm")
                require(code <= SLOTS and lexicon.slots[code - 1] is not None,
                        "unknown word reference")
                require(not previous_word, "reference is not a whole-word boundary")
                word = lexicon.slots[code - 1]
                append_bounded(output, word, MAX_OPCODE, "word")
                lexicon.observe_word(word, len(output))
                previous_word = True
                count += 1
            else:
                append_bounded(output, b"\x01", MAX_OPCODE, "word")
                previous_word = False
        elif alpha(byte):
            require(not previous_word, "literal is not a whole-word boundary")
            end = index + 1
            while end < len(data) and alpha(data[end]):
                end += 1
            word = data[index:end]
            append_bounded(output, word, MAX_OPCODE, "word")
            lexicon.observe_word(word, len(output))
            index, previous_word = end, True
        else:
            append_bounded(output, data[index:index + 1], MAX_OPCODE, "word")
            index += 1
            previous_word = False
    lexicon.bytes_seen = len(output)
    return bytes(output), {**lexicon.report(), "references": count}


def inflate(body, limit):
    """Accept exactly one bounded BZip2 member, including its checksum."""
    require(len(body) <= MAX_ARCHIVE - 5, "compressed member bound exceeded")
    try:
        decoder = bz2.BZ2Decompressor()
        raw = decoder.decompress(body, max_length=limit + 1)
    except (OSError, EOFError, ValueError) as exc:
        raise CodecError("invalid BZip2 member") from exc
    require(len(raw) <= limit, "BZip2 expansion bound exceeded")
    require(decoder.eof, "truncated BZip2 member or expansion bound exceeded")
    require(not decoder.unused_data, "trailing bytes or concatenated BZip2 members")
    return raw


def unpack_parent_words(data):
    """Bounded inverse of the unchanged parent's word format."""
    require(bool(data), "missing parent word count")
    count, index, words = data[0], 1, []
    require(count <= 64, "parent word count exceeds bound")
    for _ in range(count):
        require(index < len(data), "truncated parent dictionary")
        size = data[index]
        index += 1
        require(3 <= size <= 32 and index + size <= len(data), "invalid parent dictionary word")
        word = data[index:index + size]
        require(all(alpha(byte) for byte in word), "nonalphabetic parent dictionary word")
        words.append(word)
        index += size
    output = bytearray()
    while index < len(data):
        byte = data[index]
        index += 1
        if byte == 1:
            require(index < len(data), "truncated parent escape")
            value = data[index:index + 1]
            index += 1
        elif byte >= 128:
            require(byte - 128 < len(words), "unknown parent word reference")
            value = words[byte - 128]
        else:
            value = bytes([byte])
        append_bounded(output, value, MAX_OPCODE, "parent word")
    return bytes(output)


def undo_opcodes(data, parent):
    require(len(data) <= MAX_OPCODE, "opcode input bound exceeded")
    output, index = bytearray(), 0
    while index < len(data):
        byte = data[index]
        index += 1
        if byte:
            value = bytes([byte])
        else:
            require(index < len(data), "truncated opcode")
            code = data[index]
            index += 1
            require(code == parent.LIT0 or code in parent.D, "unknown opcode")
            value = b"\0" if code == parent.LIT0 else parent.D[code]
        append_bounded(output, value, MAX_RAW, "raw")
    return bytes(output)


def report(raw, archive, arm, word_report, packed_bytes):
    return dict(schema="gamma.enwiki9.causal-wordcode-result.v1", arm=arm,
                raw_bytes=len(raw), raw_sha256=sha(raw), archive_sha256=sha(archive),
                complete_archive_bytes=len(archive), framing_bytes=5,
                compressed_payload_bytes=len(archive) - 5,
                packed_bytes=packed_bytes, parent_source_sha256=PARENT_SHA256,
                **word_report, complete_package_bytes=None,
                qualification_authority=False, score_credit_bytes=0)


def encode(raw, arm="T"):
    require(type(raw) is bytes and len(raw) <= MAX_RAW, "raw input bound or type differs")
    require(arm in ARMS, "unknown arm")
    parent = parent_module()
    opcode = parent.tok(raw)
    require(len(opcode) <= MAX_OPCODE, "opcode output bound exceeded")
    packed, state = pack_words(opcode, references=arm == "T")
    if arm in ("P", "K"):
        archive = parent.compress(raw)
        packed_size = len(inflate(archive[5:], MAX_RAW if archive[4:5] == b"r" else MAX_PACKED))
    else:
        archive = b"OWF1" + arm.lower().encode("ascii") + bz2.compress(packed, 9)
        packed_size = len(packed)
    require(len(archive) <= MAX_ARCHIVE, "archive output bound exceeded")
    return archive, report(raw, archive, arm, state, packed_size)


def decode(archive, arm=None):
    require(type(archive) is bytes and 5 <= len(archive) <= MAX_ARCHIVE,
            "archive input bound or type differs")
    parent = parent_module()
    magic, mode = archive[:4], archive[4:5]
    if magic == b"OWB1" and mode in (b"r", b"w"):
        actual = "P" if arm is None else arm
        require(actual in ("P", "K"), "parent archive arm differs")
        packed = inflate(archive[5:], MAX_RAW if mode == b"r" else MAX_PACKED)
        raw = packed if mode == b"r" else undo_opcodes(unpack_parent_words(packed), parent)
        require(len(raw) <= MAX_RAW, "raw output bound exceeded")
        _, state = pack_words(parent.tok(raw), references=False)
    elif magic == b"OWF1" and mode in (b"t", b"l"):
        actual = mode.decode("ascii").upper()
        require(arm is None or arm == actual, "causal archive arm differs")
        packed = inflate(archive[5:], MAX_PACKED)
        opcode, state = unpack_words(packed, references=actual == "T")
        raw = undo_opcodes(opcode, parent)
        # Literal opcode spellings must be canonical or future word states could
        # diverge from a fresh encoding of the reconstructed input.
        require(parent.tok(raw) == opcode, "noncanonical opcode representation")
    else:
        raise CodecError("unknown archive header")
    return raw, report(raw, archive, actual, state, len(packed))


def repeat(raw, arm="T"):
    """A fresh encode: no predictor or dictionary state is reused."""
    return encode(raw, arm)


def compress_arm(data, arm):
    global LAST_REPORT
    archive, LAST_REPORT = encode(data, arm)
    return archive


def decompress_arm(data, arm):
    global LAST_REPORT
    raw, LAST_REPORT = decode(data, arm)
    return raw


def stats():
    return dict(LAST_REPORT)


def bounded_read(path, maximum):
    with Path(path).open("rb") as source:
        data = source.read(maximum + 1)
    require(len(data) <= maximum, "input file exceeds bound")
    return data


def publish(path, data):
    """Publish a complete new file; an existing target is never replaced."""
    path = Path(path)
    require(not path.exists(), "output already exists")
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode", "repeat"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args(argv)
    try:
        started_wall, started_cpu = time.perf_counter(), time.process_time()
        if args.operation == "decode":
            payload, receipt = decode(bounded_read(args.input, MAX_ARCHIVE), args.arm)
        else:
            operation = repeat if args.operation == "repeat" else encode
            payload, receipt = operation(bounded_read(args.input, MAX_RAW), args.arm or "T")
        receipt.update(operation=args.operation, codec_cpu_seconds=time.process_time() - started_cpu,
                       codec_wall_seconds=time.perf_counter() - started_wall,
                       process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        publish(args.output, payload)
        print(json.dumps(receipt, sort_keys=True))
    except (CodecError, OSError) as exc:
        parser.exit(1, f"codec refused: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
