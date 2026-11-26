#!/usr/bin/env python3
"""Archive format, parsers and table fitting for objective-holdout-v1.

Python 3 standard library only. FORMAT.md is the specification; this file is
the trainer's implementation of it. The independent decoder is written from
FORMAT.md alone and shares no code with this file.
"""
import heapq

MAGIC = b'BOH1'
MAX_ENTRY_LEN = 16
MAX_TABLE_PASSES = 15


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def read_varint(buf, pos):
    shift = 0
    value = 0
    while True:
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not b & 0x80:
            return value, pos
        shift += 7


def huffman_lengths(counts):
    """Code lengths of an optimal prefix code. counts: list of ints, all >= 1.

    Deterministic: ties are broken by creation order (leaves in symbol order,
    then internal nodes in the order they are formed).
    """
    n = len(counts)
    if n == 1:
        return [1]
    heap = [(c, i) for i, c in enumerate(counts)]
    heapq.heapify(heap)
    parent = [-1] * (2 * n - 1)
    nxt = n
    while len(heap) > 1:
        c1, a = heapq.heappop(heap)
        c2, b = heapq.heappop(heap)
        parent[a] = nxt
        parent[b] = nxt
        heapq.heappush(heap, (c1 + c2, nxt))
        nxt += 1
    depth = [0] * (2 * n - 1)
    for node in range(2 * n - 3, -1, -1):
        depth[node] = depth[parent[node]] + 1
    lengths = depth[:n]
    top = max(lengths)
    if sum(1 << (top - l) for l in lengths) != 1 << top:
        raise AssertionError('Kraft sum is not exactly one')
    return lengths


def canonical_codes(lengths):
    """Canonical codes: symbols ordered by (length, symbol index)."""
    order = sorted(range(len(lengths)), key=lambda s: (lengths[s], s))
    codes = [0] * len(lengths)
    code = 0
    prev = lengths[order[0]]
    for s in order:
        code <<= lengths[s] - prev
        prev = lengths[s]
        codes[s] = code
        code += 1
    return codes


def build_header(entries, lengths):
    if len(lengths) != len(entries) + 2:
        raise ValueError('one code length per entry, then ESC, then EOF')
    out = bytearray(MAGIC)
    out += varint(len(entries))
    for e in entries:
        if not 1 <= len(e) <= MAX_ENTRY_LEN:
            raise ValueError('entry length out of range')
        out.append(len(e))
        out += e
    if max(lengths) > 255 or min(lengths) < 1:
        raise ValueError('code length out of range')
    out += bytes(lengths)
    return bytes(out)


def parse_header(buf):
    if buf[:4] != MAGIC:
        raise ValueError('bad magic')
    n, pos = read_varint(buf, 4)
    entries = []
    for _ in range(n):
        ln = buf[pos]
        entries.append(bytes(buf[pos + 1:pos + 1 + ln]))
        pos += 1 + ln
    lengths = list(buf[pos:pos + n + 2])
    pos += n + 2
    return entries, lengths, pos


class Dictionary:
    """Entries in stored order. Symbol ids: entry i -> i, ESC -> n, EOF -> n + 1."""

    def __init__(self, entries):
        if len(set(entries)) != len(entries):
            raise ValueError('duplicate entry')
        self.entries = list(entries)
        self.n = len(entries)
        self.ESC = self.n
        self.EOF = self.n + 1
        self.single = [-1] * 256
        self.multi = {}
        self.prefix2 = set()
        lens = set()
        for i, e in enumerate(entries):
            if len(e) == 1:
                self.single[e[0]] = i
            else:
                self.multi[e] = i
                self.prefix2.add(e[:2])
                lens.add(len(e))
        self.multi_lens = sorted(lens)

    def edges(self, raw):
        """edges[i] = [(length, symbol), ...] for every entry matching at i,
        shortest first. A byte with no single-byte entry gets (1, ESC)."""
        n = len(raw)
        single = self.single
        multi = self.multi
        prefix2 = self.prefix2
        lens = self.multi_lens
        esc = self.ESC
        out = []
        for i in range(n):
            s = single[raw[i]]
            here = [(1, s if s >= 0 else esc)]
            if raw[i:i + 2] in prefix2:
                for l in lens:
                    if i + l > n:
                        break
                    sym = multi.get(raw[i:i + l])
                    if sym is not None:
                        here.append((l, sym))
            out.append(here)
        return out


def parse_tokens(edges):
    """Exact minimum number of tokens. An escaped byte is one token.
    Returns the symbol list. Ties keep the first edge found (start ascending,
    then length ascending)."""
    n = len(edges)
    big = n + 1
    best = [big] * (n + 1)
    prev = [None] * (n + 1)
    best[0] = 0
    for i in range(n):
        c = best[i] + 1
        for l, sym in edges[i]:
            j = i + l
            if c < best[j]:
                best[j] = c
                prev[j] = (i, sym)
    out = []
    at = n
    while at > 0:
        at, sym = prev[at]
        out.append(sym)
    out.reverse()
    return out


def parse_bits(edges, lengths, esc, banned=-1):
    """Exact minimum code bits for fixed code lengths; ties prefer fewer tokens.
    An escape costs lengths[esc] + 8 bits. `banned` removes one entry."""
    n = len(edges)
    inf = 1 << 60
    bits = [inf] * (n + 1)
    toks = [0] * (n + 1)
    prev = [None] * (n + 1)
    bits[0] = 0
    esc_cost = lengths[esc] + 8
    for i in range(n):
        b0 = bits[i]
        t1 = toks[i] + 1
        for l, sym in edges[i]:
            if sym == banned:
                continue
            j = i + l
            c = b0 + (esc_cost if sym == esc else lengths[sym])
            if c < bits[j] or (c == bits[j] and t1 < toks[j]):
                bits[j] = c
                toks[j] = t1
                prev[j] = (i, sym)
    out = []
    at = n
    while at > 0:
        at, sym = prev[at]
        out.append(sym)
    out.reverse()
    return out, bits[n]


def fit_table(dictionary, files_edges):
    """Code lengths fitted on training files only.

    Start from the minimum-token parse. Every entry and ESC is floored at a
    count of one so that each has a code; EOF counts the files. Then reparse
    for minimum bits under the current lengths and refit, keeping a pass only
    if it strictly lowers the training payload bits, for at most
    MAX_TABLE_PASSES passes. Returns (lengths, counts, payload_bits, passes).
    """
    n = dictionary.n
    esc = dictionary.ESC
    eof = dictionary.EOF

    def lengths_of(counts):
        return huffman_lengths([c if c > 0 else 1 for c in counts])

    def cost(counts, lengths):
        return sum(c * l for c, l in zip(counts, lengths)) + 8 * counts[esc]

    counts = [0] * (n + 2)
    for edges in files_edges:
        for sym in parse_tokens(edges):
            counts[sym] += 1
    counts[eof] = len(files_edges)
    lengths = lengths_of(counts)
    bits = cost(counts, lengths)
    passes = 0
    for step in range(1, MAX_TABLE_PASSES + 1):
        c2 = [0] * (n + 2)
        for edges in files_edges:
            syms, _ = parse_bits(edges, lengths, esc)
            for sym in syms:
                c2[sym] += 1
        c2[eof] = len(files_edges)
        l2 = lengths_of(c2)
        b2 = cost(c2, l2)
        if b2 < bits:
            counts, lengths, bits, passes = c2, l2, b2, step
        else:
            break
    return lengths, counts, bits, passes


class BitWriter:
    def __init__(self):
        self.out = bytearray()
        self.acc = 0
        self.nbits = 0

    def put(self, code, length):
        self.acc = (self.acc << length) | code
        self.nbits += length
        while self.nbits >= 8:
            self.nbits -= 8
            self.out.append((self.acc >> self.nbits) & 0xFF)
        self.acc &= (1 << self.nbits) - 1

    def finish(self):
        if self.nbits:
            self.out.append((self.acc << (8 - self.nbits)) & 0xFF)
            self.acc = 0
            self.nbits = 0
        return bytes(self.out)


def encode_payload(dictionary, lengths, files, parses):
    """files: raw bytes per file; parses: symbol list per file (ESC symbols
    consume one source byte each). Returns (payload bytes, bit count per file)."""
    codes = canonical_codes(lengths)
    esc = dictionary.ESC
    eof = dictionary.EOF
    entries = dictionary.entries
    writer = BitWriter()
    per_file = []
    for raw, syms in zip(files, parses):
        pos = 0
        nb = 0
        for sym in syms:
            writer.put(codes[sym], lengths[sym])
            nb += lengths[sym]
            if sym == esc:
                writer.put(raw[pos], 8)
                nb += 8
                pos += 1
            else:
                pos += len(entries[sym])
        if pos != len(raw):
            raise AssertionError('parse does not cover the file')
        writer.put(codes[eof], lengths[eof])
        nb += lengths[eof]
        per_file.append(nb)
    return writer.finish(), per_file


def decode_archive(buf):
    """The trainer's own decoder, used only as a self-check. The reported
    decode check is the independent decoder's."""
    entries, lengths, pos = parse_header(buf)
    n_files, pos = read_varint(buf, pos)
    n = len(entries)
    esc, eof = n, n + 1
    codes = canonical_codes(lengths)
    table = {(lengths[s], codes[s]): s for s in range(n + 2)}
    files = []
    cur = bytearray()
    code = 0
    length = 0
    bitpos = pos * 8
    total = len(buf) * 8

    def bit():
        nonlocal bitpos
        if bitpos >= total:
            raise ValueError('truncated payload')
        b = (buf[bitpos >> 3] >> (7 - (bitpos & 7))) & 1
        bitpos += 1
        return b

    while len(files) < n_files:
        code = (code << 1) | bit()
        length += 1
        sym = table.get((length, code))
        if sym is None:
            continue
        code = 0
        length = 0
        if sym == eof:
            files.append(bytes(cur))
            cur = bytearray()
        elif sym == esc:
            v = 0
            for _ in range(8):
                v = (v << 1) | bit()
            cur.append(v)
        else:
            cur += entries[sym]
    return files
