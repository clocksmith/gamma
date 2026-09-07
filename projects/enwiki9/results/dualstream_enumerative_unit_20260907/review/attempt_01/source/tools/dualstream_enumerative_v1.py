#!/usr/bin/env python3
"""Exact byte-alphabet enumeration of fixed D2GRAM programs, with its own inverse.

This codec changes section storage, not grammar selection. Rank widths use exact
integers; every count table and length is transmitted. Decoder needs no selected
archive, raw population, learned model, or grammar-discovery invocation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import struct
import sys
import time

CORE_PATH = Path(__file__).with_name("dualstream_grammar_v1.py")
spec = importlib.util.spec_from_file_location(__name__ + "_raw_core", CORE_PATH)
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
require = core.require
MAGIC = b"D2ENUM01"
HEADER = struct.Struct("<8sBIIIQ")
CHUNK = 4096
NAMES = ("literal_definitions", "grammar_programs", "structure", "content", "arguments")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity_section(data):
    require(len(data) <= core.MAX_SECTION, "raw section bound")
    return data


# An isolated interpreter instance: ordinary imports and sealed modules are not
# patched. Its bytecode retains the original grammar and expansion checks.
core.inflate = identity_section


class Counts:
    """Fenwick counts; ranks stay arbitrary precision but symbols stay bytes."""
    def __init__(self, values):
        self.tree = [0] * 257
        for symbol, count in enumerate(values):
            self.add(symbol, count)

    def add(self, symbol, delta):
        i = symbol + 1
        while i <= 256:
            self.tree[i] += delta
            i += i & -i

    def before(self, symbol):
        result, i = 0, symbol
        while i:
            result += self.tree[i]
            i -= i & -i
        return result

    def select(self, index):
        symbol, step = 0, 256
        while step:
            nxt = symbol + step
            if nxt <= 256 and self.tree[nxt] <= index:
                index -= self.tree[nxt]
                symbol = nxt
            step >>= 1
        require(symbol < 256, "rank symbol out of range")
        return symbol


def ways(counts):
    require(len(counts) == 256 and all(type(c) is int and c >= 0 for c in counts), "invalid counts")
    remaining = sum(counts)
    require(remaining <= CHUNK, "chunk count bound")
    result = 1
    for count in counts:
        result *= math.comb(remaining, count)
        remaining -= count
    return result


def width(possibilities):
    require(type(possibilities) is int and possibilities >= 1, "invalid possibilities")
    return ((possibilities - 1).bit_length() + 7) // 8


def rank_bytes(data):
    require(len(data) <= CHUNK, "chunk bound")
    counts = [0] * 256
    for symbol in data:
        counts[symbol] += 1
    initial = ways(counts)
    orderings, remaining, rank = initial, len(data), 0
    tree = Counts(counts)
    for symbol in data:
        rank += orderings * tree.before(symbol) // remaining
        orderings = orderings * counts[symbol] // remaining
        counts[symbol] -= 1
        tree.add(symbol, -1)
        remaining -= 1
    require(orderings == 1 and 0 <= rank < initial, "rank invariant")
    return rank.to_bytes(width(initial), "big")


def unrank(counts, encoded):
    counts = list(counts)
    orderings = ways(counts)
    require(len(encoded) == width(orderings), "rank width differs")
    rank = int.from_bytes(encoded, "big")
    require(rank < orderings, "rank exceeds possible orderings")
    remaining, output = sum(counts), bytearray()
    tree = Counts(counts)
    while remaining:
        symbol = tree.select(rank * remaining // orderings)
        rank -= orderings * tree.before(symbol) // remaining
        orderings = orderings * counts[symbol] // remaining
        require(0 <= rank < orderings, "rank interval invariant")
        output.append(symbol)
        counts[symbol] -= 1
        tree.add(symbol, -1)
        remaining -= 1
    require(rank == 0 and orderings == 1, "terminal rank invariant")
    return bytes(output)


def encode_section(data):
    identity_section(data)
    header = core.uint(len(data))
    out = bytearray(header)
    ranks = tables = chunks = 0
    for start in range(0, len(data), CHUNK):
        chunk = data[start:start + CHUNK]
        counts = Counter(chunk)
        table = core.uint(len(counts)) + b"".join(bytes([s]) + core.uint(counts[s]) for s in sorted(counts))
        encoded = rank_bytes(chunk)
        out.extend(table + encoded)
        ranks += len(encoded)
        tables += len(table)
        chunks += 1
    report = dict(raw_serialized_bytes=len(data), raw_serialized_sha256=sha(data), rank_bytes=ranks,
                  count_table_bytes=tables, stream_header_bytes=len(header), chunks=chunks,
                  encoded_bytes=len(out))
    require(ranks + tables + len(header) == len(out), "section accounting")
    return bytes(out), report


def decode_section(encoded):
    reader = core.Reader(encoded)
    size = reader.number(core.MAX_SECTION)
    out = bytearray()
    while len(out) < size:
        expected = min(CHUNK, size - len(out))
        counts, previous, total = [0] * 256, -1, 0
        entries = reader.number(256)
        require(1 <= entries <= expected, "alphabet size bound")
        for _ in range(entries):
            symbol = reader.take(1)[0]
            count = reader.number(expected)
            require(symbol > previous and count > 0, "unordered, duplicate or zero count")
            counts[symbol], previous = count, symbol
            total += count
            require(total <= expected, "count sum bound")
        require(total == expected, "count sum differs")
        out.extend(unrank(counts, reader.take(width(ways(counts)))))
    reader.end()
    return bytes(out)


def adapt_arguments(sections, raw_size):
    """D2GRAM02 raw token arguments -> D2GRAM01 raw argument references."""
    reader = core.Reader(sections[0])
    pool = [reader.take(reader.number(core.MAX_SECTION)) for _ in range(reader.number(2 * core.MAX_FRAME))]
    reader.end()
    tokens = core.Reader(sections[4])
    values, expanded, token_count = [], 0, 0
    for _ in range(tokens.number(2 * core.MAX_FRAME)):
        count = tokens.number(2 * core.MAX_FRAME)
        token_count += count
        require(token_count <= 2 * core.MAX_FRAME, "argument token work limit")
        argument = bytearray()
        for _ in range(count):
            code = tokens.number()
            require(code & 1 == 0 and code >> 1 < len(pool), "invalid argument token reference")
            value = pool[code >> 1]
            require(len(argument) + len(value) <= raw_size, "argument expansion limit")
            argument.extend(value)
        expanded += len(argument)
        require(expanded <= core.MAX_SECTION, "total argument expansion limit")
        values.append(bytes(argument))
    tokens.end()
    ids, references = {v: i for i, v in enumerate(pool)}, []
    for value in values:
        if value not in ids:
            ids[value] = len(pool)
            pool.append(value)
        references.append(ids[value])
    definitions = core.uint(len(pool)) + b"".join(core.uint(len(v)) + v for v in pool)
    require(len(pool) <= 2 * core.MAX_FRAME and len(definitions) <= core.MAX_SECTION, "expanded dictionary bound")
    result = list(sections)
    result[0] = definitions
    result[4] = core.uint(len(references)) + b"".join(core.uint(i) for i in references)
    return tuple(result)


def decode(archive, max_output=core.MAX_RAW):
    require(len(archive) <= core.MAX_ARCHIVE, "archive size bound")
    reader = core.Reader(archive)
    magic, storage, chunk, frame_size, frames, total = HEADER.unpack(reader.take(HEADER.size))
    require(magic == MAGIC and storage in (0, 1) and chunk == CHUNK, "unknown format or chunk policy")
    require(1 <= frame_size <= core.MAX_FRAME and total <= min(max_output, core.MAX_RAW), "output or frame bound")
    require(frames == (total + frame_size - 1) // frame_size, "frame count differs")
    output, sections_digest = bytearray(), []
    for _ in range(frames):
        size, mode, *tail = core.FRAME.unpack(reader.take(core.FRAME.size))
        lengths, digest = tail[:5], tail[5]
        require(size == min(frame_size, total - len(output)) and mode in core.MODES.values(), "frame size or mode")
        require(all(n <= 2 * core.MAX_SECTION for n in lengths), "encoded section bound")
        sections = tuple(decode_section(reader.take(n)) for n in lengths)
        sections_digest.append([sha(s) for s in sections])
        if mode == core.MODES["plain"]:
            require(all(not sections[i] for i in (0, 1, 2, 4)), "plain frame has grammar sections")
            raw = sections[3]
        else:
            raw = core.interpret(adapt_arguments(sections, size) if storage else sections, size)
        require(len(raw) == size and sha(raw) == digest.hex(), "frame reconstruction hash differs")
        output.extend(raw)
    reader.end()
    require(len(output) == total, "total size differs")
    return bytes(output), dict(raw_bytes=total, raw_sha256=sha(output), section_hashes=sections_digest)


def encode(selected_archive, storage="old"):
    """Explicitly adapt a selected program; no raw encoder discovery is claimed."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import dualstream_grammar_reserialize_v1 as rep
    reserialized, fixed = rep.reserialize(selected_archive, storage)
    reader = core.Reader(reserialized)
    _, frame_size, count, total = core.HEADER.unpack(reader.take(core.HEADER.size))
    out = bytearray(HEADER.pack(MAGIC, int(storage == "new"), CHUNK, frame_size, count, total))
    frames = []
    for index in range(count):
        size, mode, *tail = core.FRAME.unpack(reader.take(core.FRAME.size))
        original = tuple(rep.old.inflate(reader.take(n)) for n in tail[:5])
        encoded, costs = zip(*(encode_section(s) for s in original))
        out.extend(core.FRAME.pack(size, mode, *(len(s) for s in encoded), tail[5]))
        out.extend(b"".join(encoded))
        require(len(out) <= core.MAX_ARCHIVE, "archive output bound")
        frames.append(dict(raw_bytes=size, raw_sha256=tail[5].hex(), mode=mode,
                           model_sha256=fixed["frames"][index]["model_sha256"],
                           repeated_argument_references=fixed["frames"][index]["repeated_argument_references"],
                           sections=dict(zip(NAMES, costs))))
    reader.end()
    expected_hashes = [[f["sections"][name]["raw_serialized_sha256"] for name in NAMES] for f in frames]
    ranks = {name + "_rank_bytes": sum(f["sections"][name]["rank_bytes"] for f in frames) for name in NAMES}
    overhead = {key: sum(s[key] for f in frames for s in f["sections"].values())
                for key in ("count_table_bytes", "stream_header_bytes")}
    costs = dict(ranks, **overhead, framing_bytes=HEADER.size + count * core.FRAME.size, exception_bytes=0)
    require(sum(costs.values()) == len(out), "complete cost certificate differs")
    return bytes(out), dict(costs=costs, complete_archive_bytes=len(out), frames=frames,
                            raw_bytes=total, raw_sha256=fixed["raw_sha256"],
                            section_hashes=expected_hashes, storage=storage,
                            source_archive_sha256=sha(selected_archive),
                            fixed_deflate_archive_bytes=len(reserialized),
                            repeat_scope="fixed-program-reserialization", raw_encoder_repeat_proved=False,
                            coding_alphabet="serialized-section bytes", chunk_bytes=CHUNK)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--storage", choices=("old", "new"), default="old")
    args = parser.parse_args()
    begin, cpu = time.monotonic(), time.process_time()
    with args.input.open("rb") as stream:
        data = stream.read(core.MAX_ARCHIVE + 1)
    require(len(data) <= core.MAX_ARCHIVE, "input bound")
    output, report = encode(data, args.storage) if args.operation == "encode" else decode(data)
    core.new_file(args.output, lambda stream: stream.write(output))
    print(json.dumps(dict(result=report, cpu_seconds=time.process_time() - cpu,
                          elapsed_seconds=time.monotonic() - begin,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == "__main__":
    main()
