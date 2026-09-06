#!/usr/bin/env python3
"""Exact shared-schema diagnostic codec; no FX2 or full-corpus equivalence claim.

WGSC0001 has a fixed header, a packed one-bit-per-block mode bitmap, and
independently terminated zlib-9 bodies. Each body has raw/coded u32 lengths and
a raw SHA256. Mode 0 is raw-block zlib; mode 1 is a zlib-compressed GSC1 program.
GSC1 contains literal spans or references to earlier decoder-derived schemas,
length-delimited arguments, and ordered (offset, delete, insert) exceptions.
No recursive calls exist: a schema is literal scaffolds interleaved with holes.

The dictionary is frozen within each block. Complete LF-terminated records,
including records spanning blocks, update it AFTER reconstruction in BOTH
modes. Initial definitions are derived from already paid reconstructed bytes;
there is no uncounted transmitted rule table or target-informed dictionary.
Unrecognized, oversized, nested, or malformed syntax remains literal bytes.

For N blocks let Bj/Gj be 8 times the actual independently terminated baseline/
grammar body lengths at that block's common dictionary state. Let H be all
header and block-envelope bits plus bitmap padding (8*ceil(N/8)-N). L/D/C choose
the shorter body, baseline on ties, so archive bits = sum min(Bj,Gj)+N+H.
P always selects Bj. This bound excludes the complete executable package and
compares RESET zlib blocks, not uninterrupted zlib or FX2. Learned dictionary
storage is a measured resource, not automatically a transmitted package.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
import zlib


MAGIC = b"WGSC0001"
GRAMMAR_MAGIC = b"GSC1"
HEADER = struct.Struct("<8sB3xIIIIQI32s")
BLOCK = struct.Struct("<II32s")
ARMS = "PLDC"
MAX_RAW = 64 * 1024 * 1024
MAX_ARCHIVE = 2 * MAX_RAW + 1024 * 1024
MAX_BLOCK = 65536
MAX_HOLES = 16
MAX_CANDIDATES = 8


class CodecError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CodecError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def u32(n):
    return struct.pack("<I", n)


def blob(value):
    return u32(len(value)) + value


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, n):
        require(0 <= n <= len(self.data) - self.pos, "truncated input")
        result = self.data[self.pos:self.pos+n]
        self.pos += n
        return result

    def number(self):
        return struct.unpack("<I", self.take(4))[0]

    def bytes(self, limit):
        n = self.number()
        require(n <= limit, "length exceeds declared limit")
        return self.take(n)

    def end(self):
        require(self.pos == len(self.data), "trailing input")


@dataclass(frozen=True)
class Schema:
    kind: bytes
    scaffolds: tuple[bytes, ...]

    @property
    def size(self):
        # Explicit conservative serialized state cost, not Python heap usage.
        return 16 + len(self.kind) + sum(4 + len(x) for x in self.scaffolds)

    def expand(self, arguments, limit):
        require(len(arguments) + 1 == len(self.scaffolds), "argument count mismatch")
        require(sum(map(len, arguments)) + sum(map(len, self.scaffolds)) <= limit,
                "expanded schema exceeds record limit")
        parts = []
        for scaffold, value in zip(self.scaffolds, arguments):
            parts.extend((scaffold, value))
        parts.append(self.scaffolds[-1])
        return b"".join(parts)


def _holes(record, kind, spans):
    if not 1 <= len(spans) <= MAX_HOLES:
        return None
    scaffolds, values, start = [], [], 0
    for left, right in spans:
        require(start <= left <= right <= len(record), "invalid parser hole")
        scaffolds.append(record[start:left])
        values.append(record[left:right])
        start = right
    scaffolds.append(record[start:])
    return Schema(kind, tuple(scaffolds)), tuple(values)


def parse_record(record):
    """Recognition only; never normalize bytes or decode XML entities in output."""
    if not record.endswith(b"\n"):
        return None
    stripped = record.strip(b" \t\r\n")
    if stripped.startswith(b"<") and b"<!" not in stripped and b"<?" not in stripped:
        try:
            root = ET.fromstring(stripped)
        except (ET.ParseError, ValueError):
            return None
        if len(root):
            return None
        opening = record.find(b"<")
        match = re.match(rb"<([A-Za-z_][A-Za-z0-9_.:-]*)", record[opening:])
        if match is None:
            return None
        name = match.group(1)
        cursor, quote, end = opening + match.end(), None, None
        spans, quote_start = [], None
        while cursor < len(record):
            value = record[cursor]
            if quote is not None:
                if value == quote:
                    spans.append((quote_start, cursor))
                    quote = None
            elif value in (34, 39):
                quote, quote_start = value, cursor + 1
            elif value == 62:
                end = cursor
                break
            cursor += 1
        if end is None:
            return None
        if record[end-1:end] != b"/":
            closing = record.rfind(b"</" + name)
            if closing <= end or b"<" in record[end+1:closing]:
                return None
            spans.append((end+1, closing))
        return _holes(record, b"xml:" + name, spans)
    if stripped.startswith(b"{{") and stripped.endswith(b"}}"):
        left = record.find(b"{{") + 2
        right = record.rfind(b"}}")
        inner = record[left:right]
        if any(x in inner for x in (b"{{", b"}}", b"[[", b"]]", b"\n", b"\r")):
            return None
        parts = inner.split(b"|")
        name = parts[0].strip(b" \t")
        if not name or len(parts) < 2:
            return None
        spans, cursor, names = [], left + len(parts[0]) + 1, set()
        for field in parts[1:]:
            equal = field.find(b"=")
            key = field[:equal].strip(b" \t") if equal >= 0 else b""
            if not key or key in names:
                return None
            names.add(key)
            spans.append((cursor + equal + 1, cursor + len(field)))
            cursor += len(field) + 1
        return _holes(record, b"wiki:" + name, spans)
    return None


class Dictionary:
    def __init__(self, max_record, max_rules, max_bytes):
        self.max_record, self.max_rules, self.max_bytes = max_record, max_rules, max_bytes
        self.rules, self.by_schema = {}, {}
        self.next_id, self.used, self.evictions = 1, 0, 0
        self.pending, self.discard = b"", False

    def add(self, record):
        parsed = parse_record(record)
        if parsed is None:
            return
        rule = parsed[0]
        if rule in self.by_schema or rule.size > self.max_bytes:
            return
        while self.rules and (len(self.rules) >= self.max_rules or self.used + rule.size > self.max_bytes):
            identifier = next(iter(self.rules))
            old = self.rules.pop(identifier)
            del self.by_schema[old]
            self.used -= old.size
            self.evictions += 1
        require(self.next_id < 1 << 64, "dictionary identifier exhausted")
        self.rules[self.next_id] = rule
        self.by_schema[rule] = self.next_id
        self.next_id += 1
        self.used += rule.size

    def update(self, raw):
        # Discard oversized records until LF, never retain an unbounded tail.
        for piece in raw.splitlines(keepends=True):
            # bytes.splitlines splits CR and other separators too; only LF
            # completes a record, so these pieces are accumulated unchanged.
            if not self.discard:
                if len(self.pending) + len(piece) > self.max_record:
                    self.pending, self.discard = b"", True
                else:
                    self.pending += piece
            if piece.endswith(b"\n"):
                if not self.discard:
                    self.add(self.pending)
                self.pending, self.discard = b"", False

    def digest(self):
        h = hashlib.sha256()
        h.update(struct.pack("<QQ?", self.next_id, self.evictions, self.discard))
        h.update(blob(self.pending))
        for identifier, rule in self.rules.items():
            h.update(struct.pack("<Q", identifier) + blob(rule.kind))
            h.update(u32(len(rule.scaffolds)))
            for part in rule.scaffolds:
                h.update(blob(part))
        return h.hexdigest()


def exception_script(base, target):
    """Canonical single middle edit: maximal prefix, then nonoverlapping suffix.

    A replace has both deletion and insertion; pure insertion/deletion have one
    zero length. This intentionally bounded realization is not a minimum edit
    distance solver. Exception positions refer to the ORIGINAL expanded base.
    """
    if base == target:
        return ()
    left = 0
    while left < min(len(base), len(target)) and base[left] == target[left]:
        left += 1
    right = 0
    while (right < min(len(base), len(target)) - left and
           base[len(base)-1-right] == target[len(target)-1-right]):
        right += 1
    return ((left, len(base)-left-right, target[left:len(target)-right if right else None]),)


def apply_exceptions(base, edits, limit):
    chunks, cursor, total = [], 0, 0
    for offset, deleted, inserted in edits:
        require(cursor <= offset <= len(base), "unordered exception offset")
        require(deleted <= len(base) - offset, "exception deletion outside base")
        require(deleted or inserted, "empty exception")
        piece = base[cursor:offset]
        total += len(piece) + len(inserted)
        require(total <= limit, "exception expansion exceeds limit")
        chunks.extend((piece, inserted))
        cursor = offset + deleted
    total += len(base) - cursor
    require(total <= limit, "exception expansion exceeds limit")
    chunks.append(base[cursor:])
    return b"".join(chunks)


def literal(raw):
    return b"\0" + blob(raw)


def reference(identifier, rule, arguments, raw, max_record):
    base = rule.expand(arguments, max_record)
    edits = exception_script(base, raw)
    out = bytearray(b"\1" + struct.pack("<Q", identifier) + u32(len(arguments)))
    for arg in arguments:
        out += blob(arg)
    out += u32(len(edits))
    for offset, deleted, inserted in edits:
        out += u32(offset) + u32(deleted) + blob(inserted)
    require(apply_exceptions(base, edits, max_record) == raw, "encoder exception check failed")
    return bytes(out), len(edits)


def grammar(raw, dictionary, arm):
    stats = {"references": 0, "exceptions": 0, "literal_bytes": 0,
             "eligible_records": 0, "shuffled_associations": 0,
             "shuffled_queries": 0}
    records, start = [], 0
    for end in range(len(raw)):
        if raw[end] == 10:
            records.append(raw[start:end+1])
            start = end+1
    if start < len(raw):
        records.append(raw[start:])
    output = bytearray(GRAMMAR_MAGIC + u32(len(records)))
    first_fragment = bool(dictionary.pending) or dictionary.discard
    for index, record in enumerate(records):
        choice, edits_count, changed = literal(record), 0, False
        parsed = None if arm == "L" or (index == 0 and first_fragment) or len(record) > dictionary.max_record else parse_record(record)
        if parsed is not None:
            schema, arguments = parsed
            eligible = [(identifier, rule) for identifier, rule in dictionary.rules.items()
                        if rule.kind == schema.kind and len(rule.scaffolds) == len(schema.scaffolds)]
            eligible = eligible[-MAX_CANDIDATES:]
            candidates = []
            for identifier, rule in eligible:
                try:
                    encoded, count = reference(identifier, rule, arguments, record, dictionary.max_record)
                except CodecError:
                    continue
                candidates.append((encoded, identifier, count, rule))
            if candidates:
                stats["eligible_records"] += 1
                # Paid identifiers resolve ambiguity; tie uses the oldest ID.
                best = min(candidates, key=lambda row: (len(row[0]), row[1]))
                if arm == "C" and len(candidates) > 1:
                    at = next(i for i, row in enumerate(candidates) if row[1] == best[1])
                    best = candidates[(at + 1) % len(candidates)]
                    changed = True
                    stats["shuffled_queries"] += 1
                if len(best[0]) < len(choice):
                    choice, edits_count = best[0], best[2]
        output += choice
        if choice[0] == 1:
            stats["references"] += 1
            stats["exceptions"] += edits_count
            stats["shuffled_associations"] += int(changed)
        else:
            stats["literal_bytes"] += len(record)
    return bytes(output), stats


def decode_grammar(program, dictionary, expected):
    reader = Reader(program)
    require(reader.take(4) == GRAMMAR_MAGIC, "unknown grammar format")
    count = reader.number()
    require(1 <= count <= expected + 1, "invalid segment count")
    chunks, size = [], 0
    for _ in range(count):
        opcode = reader.take(1)[0]
        if opcode == 0:
            value = reader.bytes(expected)
            require(value, "empty literal")
        elif opcode == 1:
            identifier = struct.unpack("<Q", reader.take(8))[0]
            require(identifier in dictionary.rules, "unknown or evicted schema identifier")
            rule = dictionary.rules[identifier]
            n = reader.number()
            require(n == len(rule.scaffolds) - 1, "argument count mismatch")
            arguments = tuple(reader.bytes(dictionary.max_record) for _ in range(n))
            base = rule.expand(arguments, dictionary.max_record)
            n = reader.number()
            require(n <= dictionary.max_record, "too many exceptions")
            edits = tuple((reader.number(), reader.number(), reader.bytes(dictionary.max_record)) for _ in range(n))
            value = apply_exceptions(base, edits, dictionary.max_record)
            require(value, "empty reference expansion")
        else:
            raise CodecError("unknown program opcode")
        size += len(value)
        require(size <= expected, "block expansion exceeds expected length")
        chunks.append(value)
    reader.end()
    require(size == expected, "block expansion length mismatch")
    return b"".join(chunks)


def limits(block_size, max_record, max_rules, max_dictionary_bytes):
    require(type(block_size) is int and 64 <= block_size <= MAX_BLOCK, "invalid block size")
    require(type(max_record) is int and 64 <= max_record <= MAX_BLOCK, "invalid record limit")
    require(type(max_rules) is int and 1 <= max_rules <= 4096, "invalid rule limit")
    require(type(max_dictionary_bytes) is int and 64 <= max_dictionary_bytes <= 16*1024*1024,
            "invalid dictionary byte limit")


def receipt_base(raw, archive, arm, rows):
    return {"schema": "gamma.wiki-schema-exact-codec.v1", "arm": arm,
            "baseline": "stdlib zlib level 9, independently reset fixed raw blocks",
            "zlib_version": zlib.ZLIB_RUNTIME_VERSION,
            "raw_bytes": len(raw), "raw_sha256": sha(raw),
            "archive_bytes": len(archive), "archive_sha256": sha(archive),
            "blocks": rows, "complete_executable_package_bytes": None,
            "full_corpus_score_bytes": None, "score_credit_bytes": 0,
            "uninterrupted_fx2_equivalence_claimed": False,
            "dictionary_rule_origin": "deterministically derived from earlier paid complete raw records"}


def encode(raw, *, arm="D", block_size=4096, max_record=4096, max_rules=256,
           max_dictionary_bytes=1048576):
    require(type(raw) is bytes and len(raw) <= MAX_RAW, "raw input exceeds bounded gate")
    require(type(arm) is str and len(arm) == 1 and arm in ARMS, "unknown arm")
    limits(block_size, max_record, max_rules, max_dictionary_bytes)
    n = (len(raw) + block_size - 1) // block_size
    bitmap, bodies, rows = bytearray((n+7)//8), [], []
    dictionary = Dictionary(max_record, max_rules, max_dictionary_bytes)
    for index, start in enumerate(range(0, len(raw), block_size)):
        block = raw[start:start+block_size]
        before = dictionary.digest()
        baseline = zlib.compress(block, 9)
        alternative, stats = None, {"evaluated": False}
        if arm != "P":
            program, stats = grammar(block, dictionary, arm)
            stats["evaluated"] = True
            alternative = zlib.compress(program, 9)
        mode = int(alternative is not None and len(alternative) < len(baseline))
        body = alternative if mode else baseline
        bitmap[index//8] |= mode << (index%8)
        bodies.append(BLOCK.pack(len(block), len(body), hashlib.sha256(block).digest()) + body)
        dictionary.update(block)
        rows.append({"index": index, "raw_bytes": len(block), "baseline_bits": 8*len(baseline),
                     "grammar_bits": 8*len(alternative) if alternative is not None else None, "selected_bits": 8*len(body),
                     "mode": mode, "dictionary_before": before, "dictionary_after": dictionary.digest(),
                     "dictionary_rules": len(dictionary.rules), "dictionary_serialized_bytes": dictionary.used,
                     "dictionary_evictions": dictionary.evictions, "grammar_proposal": stats})
    header = HEADER.pack(MAGIC, ARMS.index(arm), block_size, max_record, max_rules,
                         max_dictionary_bytes, len(raw), n, hashlib.sha256(raw).digest())
    archive = header + bytes(bitmap) + b"".join(bodies)
    common = 8*(HEADER.size + n*BLOCK.size) + 8*len(bitmap) - n
    rhs = (sum(min(row["baseline_bits"], row["grammar_bits"]) for row in rows) + n + common) if arm != "P" else None
    receipt = receipt_base(raw, archive, arm, rows)
    receipt["accounting"] = {"archive_bits": 8*len(archive), "mode_bits": n,
        "bitmap_padding_bits": 8*len(bitmap)-n, "H_bits": common,
        "sum_min_Bj_Gj_plus_N_plus_H_bits": rhs, "bound_applies": arm != "P",
        "bound_pass": 8*len(archive) <= rhs if arm != "P" else None,
        "equivalent_framed_baseline_bytes": HEADER.size+len(bitmap)+n*BLOCK.size+sum(row["baseline_bits"]//8 for row in rows),
        "package_accounted_separately": True}
    require(arm == "P" or receipt["accounting"]["bound_pass"], "internal block bound failure")
    return archive, receipt


def inflate(body, limit):
    try:
        decoder = zlib.decompressobj()
        value = decoder.decompress(body, limit+1)
    except zlib.error as exc:
        raise CodecError("invalid independently terminated zlib body") from exc
    require(len(value) <= limit, "decompressed body exceeds limit")
    require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
            "truncated or trailing compressed body")
    return value


def decode_archive(archive):
    require(type(archive) is bytes and len(archive) <= MAX_ARCHIVE, "archive exceeds bounded gate")
    reader = Reader(archive)
    magic, arm_id, block_size, max_record, max_rules, max_bytes, total, n, digest = HEADER.unpack(reader.take(HEADER.size))
    require(magic == MAGIC and arm_id < len(ARMS), "unknown archive format or arm")
    require(archive[9:12] == b"\0\0\0", "nonzero reserved header")
    limits(block_size, max_record, max_rules, max_bytes)
    require(total <= MAX_RAW and n == (total+block_size-1)//block_size, "invalid block population")
    bitmap = reader.take((n+7)//8)
    require(not n or not n % 8 or bitmap[-1] >> (n % 8) == 0, "nonzero bitmap padding")
    arm, dictionary = ARMS[arm_id], Dictionary(max_record, max_rules, max_bytes)
    output, rows = [], []
    for index in range(n):
        raw_size, coded_size, raw_digest = BLOCK.unpack(reader.take(BLOCK.size))
        expected = min(block_size, total-index*block_size)
        require(raw_size == expected and 1 <= coded_size <= 16*block_size+4096, "invalid block envelope")
        mode = (bitmap[index//8] >> (index%8)) & 1
        require(arm != "P" or mode == 0, "baseline arm contains a grammar block")
        before = dictionary.digest()
        body = reader.take(coded_size)
        program = inflate(body, 16*block_size+4096 if mode else raw_size)
        block = decode_grammar(program, dictionary, raw_size) if mode else program
        require(len(block) == raw_size and hashlib.sha256(block).digest() == raw_digest,
                "raw block length or digest mismatch")
        # A malformed L archive cannot silently activate references.
        if mode and arm == "L":
            require(program == grammar(block, dictionary, "L")[0], "literal-only arm program mismatch")
        dictionary.update(block)
        output.append(block)
        rows.append({"index": index, "mode": mode, "dictionary_before": before,
                     "dictionary_after": dictionary.digest()})
    reader.end()
    raw = b"".join(output)
    require(len(raw) == total and hashlib.sha256(raw).digest() == digest, "complete raw digest mismatch")
    return raw, receipt_base(raw, archive, arm, rows)


def decode(archive):
    return decode_archive(archive)[0]


def read_bounded(path, limit):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "input must be a regular file")
    require(before.st_size <= limit, "input file exceeds bounded gate")

    def identity(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                info.st_mtime_ns, info.st_ctime_ns)

    # O_NONBLOCK prevents a raced replacement FIFO from blocking during open;
    # O_NOFOLLOW rejects a raced final-component symlink before it is followed.
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        require(identity(os.fstat(descriptor)) == identity(before), "input changed before read")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            value = handle.read(limit+1)
        require(identity(os.fstat(descriptor)) == identity(before)
                and identity(path.lstat()) == identity(before), "input changed during read")
    finally:
        os.close(descriptor)
    require(len(value) == before.st_size and len(value) <= limit,
            "input length changed or exceeds bounded gate")
    return value


def publish(path, data):
    """Close and fsync an owned temporary, then link exclusively; never replace."""
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="."+path.name+".", delete=False) as handle:
            temporary = Path(handle.name)
            require(handle.write(data) == len(data), "short output write")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encode")
    enc.add_argument("input")
    enc.add_argument("output")
    enc.add_argument("--arm", choices=list(ARMS), default="D")
    enc.add_argument("--block-size", type=int, default=4096)
    enc.add_argument("--max-record", type=int, default=4096)
    enc.add_argument("--max-rules", type=int, default=256)
    enc.add_argument("--max-dictionary-bytes", type=int, default=1048576)
    enc.add_argument("--receipt")
    dec = sub.add_parser("decode")
    dec.add_argument("input")
    dec.add_argument("output")
    dec.add_argument("--receipt")
    args = parser.parse_args(argv)
    try:
        if args.command == "encode":
            raw = read_bounded(args.input, MAX_RAW)
            result, receipt = encode(raw, arm=args.arm, block_size=args.block_size,
                max_record=args.max_record, max_rules=args.max_rules,
                max_dictionary_bytes=args.max_dictionary_bytes)
            require(decode(result) == raw, "encoder independent decode failed")
        else:
            result, receipt = decode_archive(read_bounded(args.input, MAX_ARCHIVE))
        publish(args.output, result)
        if args.receipt:
            publish(args.receipt, (json.dumps(receipt, sort_keys=True, indent=2)+"\n").encode())
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (CodecError, OSError, struct.error) as exc:
        print("schema codec error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
