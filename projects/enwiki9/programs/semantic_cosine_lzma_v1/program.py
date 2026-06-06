"""semantic_cosine_lzma_v1.

Self-referential semantic/byte codec:
  1. Words form an online graph.
  2. A word may reference a prior nearest word by character n-gram overlap.
  3. The archive stores only the byte patch from that prior word.
  4. The decoder rebuilds the same word graph from decoded bytes.

The graph is finite and acyclic because every reference points backward.
"""

from __future__ import annotations

import lzma
import re
from collections import Counter

S_ESC = 1
S_LIT_ESC = 255
TAG_PREF = 64
TAG_SUFF = 65
O_ESC = 0
O_LIT_ESC = 255
PRESET = 9 | lzma.PRESET_EXTREME

MIN_WORD = 4
MAX_WORD = 40
MAX_POSTINGS = 96
MIN_OVERLAP = 2

WORD_RE = re.compile(rb"[A-Za-z][A-Za-z'-]{2,39}")

TOKENS = [
    b'<text xml:space="preserve">',
    b"</text>",
    b"<page>",
    b"</page>",
    b"<revision>",
    b"</revision>",
    b"<contributor>",
    b"</contributor>",
    b"<timestamp>",
    b"</timestamp>",
    b"<username>",
    b"</username>",
    b"<comment>",
    b"</comment>",
    b"<title>",
    b"</title>",
    b"<id>",
    b"</id>",
    b"<minor />",
    b"{{",
    b"}}",
    b"[[Category:",
    b"[[Image:",
    b"[[",
    b"]]",
    b"&quot;",
    b"&lt;",
    b"&gt;",
    b"&amp;",
    b"http://",
    b"https://",
    b"<ref",
    b"</ref>",
    b"|thumb",
    b"|right",
    b"|left",
    b"Category:",
    b"File:",
    b"Image:",
]

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
TOKEN_DECODE = dict(enumerate(TOKENS, 1))
LAST_STATS: dict[str, int] = {}


def _varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    value = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated varint")
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint too large")


def _grams(word: bytes) -> set[bytes]:
    w = b"^" + word.lower() + b"$"
    return {w[i : i + 2] for i in range(len(w) - 1)}


def _common_prefix(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _common_suffix(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[len(a) - 1 - i] == b[len(b) - 1 - i]:
        i += 1
    return i


def _emit_raw(out: bytearray, chunk: bytes) -> None:
    for b in chunk:
        if b == S_ESC:
            out.extend((S_ESC, S_LIT_ESC))
        else:
            out.append(b)


def _encoded_ref(tag: int, idx: int, keep: int, add: bytes) -> bytes:
    return bytes((S_ESC, tag)) + _varint(idx) + _varint(keep) + _varint(len(add)) + add


class _EncoderGraph:
    def __init__(self) -> None:
        self.words: list[bytes] = []
        self.word_grams: list[set[bytes]] = []
        self.gram_index: dict[bytes, list[int]] = {}

    def add(self, word: bytes) -> None:
        if not (MIN_WORD <= len(word) <= MAX_WORD):
            return
        idx = len(self.words)
        grams = _grams(word)
        self.words.append(word)
        self.word_grams.append(grams)
        for gram in grams:
            posting = self.gram_index.setdefault(gram, [])
            posting.append(idx)
            if len(posting) > MAX_POSTINGS:
                del posting[0]

    def best_ref(self, word: bytes) -> bytes | None:
        if not (MIN_WORD <= len(word) <= MAX_WORD):
            return None
        grams = _grams(word)
        hits: Counter[int] = Counter()
        for gram in grams:
            for idx in self.gram_index.get(gram, ()):
                hits[idx] += 1
        if not hits:
            return None

        best: bytes | None = None
        best_len = len(word)
        for idx, overlap in hits.most_common(48):
            if overlap < MIN_OVERLAP:
                continue
            base = self.words[idx]
            pref = _common_prefix(base, word)
            if pref:
                candidate = _encoded_ref(TAG_PREF, idx, pref, word[pref:])
                if len(candidate) < best_len:
                    best = candidate
                    best_len = len(candidate)
            suff = _common_suffix(base, word)
            if suff:
                candidate = _encoded_ref(TAG_SUFF, idx, suff, word[: len(word) - suff])
                if len(candidate) < best_len:
                    best = candidate
                    best_len = len(candidate)
        return best


def _semantic_encode(data: bytes) -> bytes:
    graph = _EncoderGraph()
    out = bytearray()
    pos = 0
    literal_words = ref_words = ref_source_bytes = ref_encoded_bytes = 0

    for match in WORD_RE.finditer(data):
        word = match.group(0)
        _emit_raw(out, data[pos : match.start()])
        encoded = graph.best_ref(word)
        if encoded is None:
            _emit_raw(out, word)
            literal_words += 1
        else:
            out.extend(encoded)
            ref_words += 1
            ref_source_bytes += len(word)
            ref_encoded_bytes += len(encoded)
        graph.add(word)
        pos = match.end()

    _emit_raw(out, data[pos:])
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "semantic_size": len(out),
            "word_graph_size": len(graph.words),
            "literal_word_count": literal_words,
            "ref_word_count": ref_words,
            "ref_source_bytes": ref_source_bytes,
            "ref_encoded_bytes": ref_encoded_bytes,
        }
    )
    return bytes(out)


def _scan_words_into(words: list[bytes], chunk: bytes) -> None:
    for match in WORD_RE.finditer(chunk):
        word = match.group(0)
        if MIN_WORD <= len(word) <= MAX_WORD:
            words.append(word)


def _semantic_decode(stream: bytes) -> bytes:
    words: list[bytes] = []
    raw = bytearray()
    out = bytearray()
    i = 0
    n = len(stream)

    def flush_raw() -> None:
        if raw:
            chunk = bytes(raw)
            out.extend(chunk)
            _scan_words_into(words, chunk)
            raw.clear()

    while i < n:
        b = stream[i]
        if b != S_ESC:
            raw.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated semantic escape")
        tag = stream[i + 1]
        i += 2
        if tag == S_LIT_ESC:
            raw.append(S_ESC)
            continue

        flush_raw()
        idx, i = _read_varint(stream, i)
        keep, i = _read_varint(stream, i)
        add_len, i = _read_varint(stream, i)
        add = stream[i : i + add_len]
        if len(add) != add_len:
            raise ValueError("truncated word patch")
        i += add_len
        base = words[idx]
        if tag == TAG_PREF:
            word = base[:keep] + add
        elif tag == TAG_SUFF:
            word = add + base[len(base) - keep :]
        else:
            raise ValueError(f"bad semantic tag {tag:#x}")
        out.extend(word)
        if MIN_WORD <= len(word) <= MAX_WORD:
            words.append(word)

    flush_raw()
    return bytes(out)


def _opcode_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] == O_ESC:
            out.extend((O_ESC, O_LIT_ESC))
            i += 1
            continue
        for code, token in TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((O_ESC, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    LAST_STATS["opcode_size"] = len(out)
    return bytes(out)


def _opcode_decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != O_ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated opcode escape")
        code = data[i + 1]
        if code == O_LIT_ESC:
            out.append(O_ESC)
        else:
            out.extend(TOKEN_DECODE[code])
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    return lzma.compress(_opcode_encode(_semantic_encode(data)), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return _semantic_decode(_opcode_decode(lzma.decompress(data)))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
