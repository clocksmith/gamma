"""phrase_bz2_v1 — backend-aware class-ablated phrase substitution + bz2.

Per the user's challenge: do not admit phrases by raw frequency. Mine
phrases per class, run a backend ablation (raw bz2 vs phrase+bz2 on the
same input), and admit ONLY classes whose substitution makes the
bz2-compressed archive strictly smaller. Phrases that improve raw size
but worsen compressed size are killed.

Backend choice: bz2. Recent results showed bz2's BWT context-clustering
benefits more from typed-token substitution than lzma's match-based
matcher does on small/medium scope. The ablation is the arbiter.

Phrase classes (mined separately, ablated separately):
  plain_english       — multi-word natural-language n-grams
  wikilink            — [[X]] and [[X|Y]] internal-link patterns
  template_key_value  — wikitext template key= prefixes
  category            — [[Category:X]] patterns
  xml_field           — XML open/close tag tokens

Per-class admission rule:
  candidate = bz2(substitute(data, mined_phrases_for_class))
  baseline  = bz2(data)
  admit class iff len(candidate) < len(baseline)

If no class survives, archive falls through to raw bz2(data) with a
"baseline_only" mode marker. Surviving classes' phrases are pooled (up to
total code budget of 128) and applied longest-first to avoid overlap.

Archive layout:
  4B manifest_len
  manifest (JSON; provenance: schema_version, classes admitted, ablation
            results, phrase counts per class)
  4B phrase_table_len
  phrase_table (length-prefixed phrase bytes; index = code idx)
  4B body_len
  body (bz2-compressed substituted bytes; or raw bz2(data) on fallback)
"""

from __future__ import annotations

import bz2
import json
import re
import struct
from collections import Counter

BZ2_LEVEL = 9
SCHEMA_VERSION = 1
ESC = 0x01
CODE_BASE = 0x80
MAX_TOTAL_CODES = 128
PER_CLASS_TOP_K = 32
MIN_PHRASE_FREQ = 4

CLASS_ORDER = [
    "xml_field",
    "wikilink",
    "category",
    "template_key_value",
    "plain_english",
]

# Per-class miner regexes.
_RE_WIKILINK = re.compile(rb"\[\[([^\[\]|]{1,80})(?:\|[^\[\]]*)?\]\]")
_RE_CATEGORY = re.compile(rb"\[\[(Category:[^\[\]|]{1,80})\]\]")
_RE_TPL_KV   = re.compile(rb"\b([a-zA-Z_][a-zA-Z0-9_]{1,28}=)")
_RE_XML_TAG  = re.compile(rb"(<[a-z][a-z0-9_:\-]{0,30}(?:\s[^>]{0,80})?/?>|</[a-z][a-z0-9_:\-]{0,30}>)")
_RE_EN_NGRAM = re.compile(rb"\b[A-Za-z]{2,}(?:\s+[A-Za-z]{2,}){1,3}\b")


def _saving(p: bytes, f: int) -> int:
    return f * (len(p) - 1) - (1 + len(p))


def _mine_xml_field(data: bytes) -> Counter:
    c: Counter = Counter()
    for m in _RE_XML_TAG.finditer(data):
        c[m.group(0)] += 1
    return c


def _mine_wikilink(data: bytes) -> Counter:
    c: Counter = Counter()
    for m in _RE_WIKILINK.finditer(data):
        c[m.group(0)] += 1
    return c


def _mine_category(data: bytes) -> Counter:
    c: Counter = Counter()
    for m in _RE_CATEGORY.finditer(data):
        c[m.group(0)] += 1
    return c


def _mine_template_kv(data: bytes) -> Counter:
    c: Counter = Counter()
    for m in _RE_TPL_KV.finditer(data):
        c[m.group(0)] += 1
    return c


def _mine_plain_english(data: bytes) -> Counter:
    c: Counter = Counter()
    for m in _RE_EN_NGRAM.finditer(data):
        c[m.group(0)] += 1
    return c


_MINERS = {
    "xml_field": _mine_xml_field,
    "wikilink": _mine_wikilink,
    "category": _mine_category,
    "template_key_value": _mine_template_kv,
    "plain_english": _mine_plain_english,
}


def _top_phrases(counter: Counter, k: int) -> list[bytes]:
    scored: list[tuple[int, bytes]] = []
    for p, f in counter.items():
        if f < MIN_PHRASE_FREQ:
            continue
        s = _saving(p, f)
        if s > 0:
            scored.append((s, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [p for _, p in scored[:k]]


def _escape(chunk: bytes) -> bytes:
    if not any(b == ESC or b >= CODE_BASE for b in chunk):
        return chunk
    out = bytearray()
    for b in chunk:
        if b == ESC or b >= CODE_BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _substitute(data: bytes, phrases: list[bytes]) -> bytes:
    if not phrases:
        return _escape(data)
    code_map = {p: bytes([CODE_BASE + i]) for i, p in enumerate(phrases)}
    pat = re.compile(
        b"|".join(re.escape(p) for p in sorted(phrases, key=lambda x: -len(x)))
    )
    parts: list[bytes] = []
    pos = 0
    for m in pat.finditer(data):
        if m.start() > pos:
            parts.append(_escape(data[pos : m.start()]))
        parts.append(code_map[m.group(0)])
        pos = m.end()
    if pos < len(data):
        parts.append(_escape(data[pos:]))
    return b"".join(parts)


def _expand(stream: bytes, phrases: list[bytes]) -> bytes:
    out = bytearray()
    pos = 0
    n = len(stream)
    while pos < n:
        b = stream[pos]
        if b == ESC:
            pos += 1
            out.append(stream[pos])
            pos += 1
        elif b >= CODE_BASE:
            idx = b - CODE_BASE
            if idx >= len(phrases):
                raise ValueError(f"bad code {b:#x} idx={idx}")
            out.extend(phrases[idx])
            pos += 1
        else:
            out.append(b)
            pos += 1
    return bytes(out)


def _ablate_class(data: bytes, class_name: str, baseline_size: int,
                  top_k: int) -> tuple[bool, list[bytes], int]:
    """Return (admitted, mined_phrases, candidate_size)."""
    miner = _MINERS[class_name]
    counter = miner(data)
    phrases = _top_phrases(counter, top_k)
    if not phrases:
        return False, [], baseline_size
    sub = _substitute(data, phrases)
    candidate_size = len(bz2.compress(sub, BZ2_LEVEL))
    return candidate_size < baseline_size, phrases, candidate_size


def compress(data: bytes) -> bytes:
    baseline = bz2.compress(data, BZ2_LEVEL)
    baseline_size = len(baseline)

    ablation: list[dict] = []
    admitted_phrases: list[bytes] = []
    admitted_classes: list[str] = []
    admitted_counts: dict[str, int] = {}

    for cls in CLASS_ORDER:
        budget_left = MAX_TOTAL_CODES - len(admitted_phrases)
        if budget_left <= 0:
            ablation.append({"class": cls, "skipped": "budget_exhausted"})
            continue
        per_k = min(PER_CLASS_TOP_K, budget_left)
        ok, phrases, cand_size = _ablate_class(
            data, cls, baseline_size, per_k
        )
        ablation.append({
            "class": cls,
            "mined": len(phrases),
            "candidate_size": cand_size,
            "baseline_size": baseline_size,
            "admitted": ok,
        })
        if ok:
            # Filter out duplicates already admitted from earlier classes.
            new = [p for p in phrases if p not in set(admitted_phrases)]
            admitted_phrases.extend(new)
            admitted_classes.append(cls)
            admitted_counts[cls] = len(new)

    if not admitted_phrases:
        # Strict fallback: no class survived ablation. Archive carries raw
        # bz2(data) with manifest mode "baseline_only".
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "mode": "baseline_only",
            "ablation": ablation,
            "phrase_count": 0,
            "admitted_classes": [],
            "admitted_counts": {},
        }
        mbytes = json.dumps(manifest, separators=(",", ":")).encode()
        body = baseline
    else:
        # Compose: pool admitted phrases, dedupe, longest-first substitute.
        sub = _substitute(data, admitted_phrases)
        body = bz2.compress(sub, BZ2_LEVEL)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "mode": "phrase_v1",
            "ablation": ablation,
            "phrase_count": len(admitted_phrases),
            "admitted_classes": admitted_classes,
            "admitted_counts": admitted_counts,
        }
        mbytes = json.dumps(manifest, separators=(",", ":")).encode()

    # Phrase table: 4B count + per-phrase 2B length + bytes
    pt = bytearray(struct.pack(">H", len(admitted_phrases)))
    for p in admitted_phrases:
        if not 1 <= len(p) <= 65535:
            raise ValueError(f"phrase length out of range: {len(p)}")
        pt.extend(struct.pack(">H", len(p)))
        pt.extend(p)

    out = bytearray()
    out.extend(struct.pack(">I", len(mbytes)))
    out.extend(mbytes)
    out.extend(struct.pack(">I", len(pt)))
    out.extend(bytes(pt))
    out.extend(struct.pack(">I", len(body)))
    out.extend(body)
    return bytes(out)


def decompress(arch: bytes) -> bytes:
    pos = 0
    (mlen,) = struct.unpack(">I", arch[pos : pos + 4])
    pos += 4
    manifest = json.loads(arch[pos : pos + mlen])
    pos += mlen
    (ptlen,) = struct.unpack(">I", arch[pos : pos + 4])
    pos += 4
    pt = arch[pos : pos + ptlen]
    pos += ptlen
    (blen,) = struct.unpack(">I", arch[pos : pos + 4])
    pos += 4
    body = arch[pos : pos + blen]

    # Parse phrase table.
    pp = 0
    (npr,) = struct.unpack(">H", pt[pp : pp + 2])
    pp += 2
    phrases: list[bytes] = []
    for _ in range(npr):
        (L,) = struct.unpack(">H", pt[pp : pp + 2])
        pp += 2
        phrases.append(pt[pp : pp + L])
        pp += L

    if manifest["mode"] == "baseline_only":
        return bz2.decompress(body)
    if manifest["mode"] == "phrase_v1":
        sub = bz2.decompress(body)
        return _expand(sub, phrases)
    raise ValueError(f"unknown mode: {manifest['mode']}")


def stats() -> dict:
    """Optional hook for the driver to surface ablation results.
    Not stable; only meaningful right after compress() in same process."""
    return {}
