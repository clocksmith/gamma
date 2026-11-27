"""Fit-only probability models and two standalone encodings for identical typed calls."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import struct
import sys
import zlib

A2 = Path(__file__).resolve().parent.parent / "a2-recursive-frames-v1"
if str(A2) not in sys.path:
    sys.path.append(str(A2))
from ast_frames import (ArithmeticEncoder, EXPR_TAGS, STMT_TAGS, PAT_TAGS, EXPR_CONTEXTS,
                        STMT_CONTEXTS, build_cum, encode_ustr, encode_varint, quantize_weights)

NAMES = list(dict.fromkeys(["EXPR", "STMT", "PAT", "AUX", *EXPR_TAGS, *STMT_TAGS, *PAT_TAGS,
                           *EXPR_CONTEXTS, *STMT_CONTEXTS, "PAT_DECL", "PAT_PARAM"]))
NAME_ID = {s: i + 1 for i, s in enumerate(NAMES)}


def name(s):
    code = NAME_ID.get(s, 0)
    return encode_varint(code) if code else b"\0" + encode_ustr(s)


def value(v):
    if v is None:
        return b"\0"
    if isinstance(v, bool):
        return bytes([1 + int(v)])
    if isinstance(v, int):
        return bytes([3 if v >= 0 else 4]) + encode_varint(v if v >= 0 else -1-v)
    if isinstance(v, str):
        return b"\x05" + name(v)
    if isinstance(v, tuple):
        return b"\x06" + encode_varint(len(v)) + b"".join(value(i) for i in v)
    if isinstance(v, float):
        return b"\x07" + struct.pack(">d", v)
    raise ValueError(f"unsupported AST atom {type(v).__name__}")


def block(data):
    return encode_varint(len(data)) + data


@lru_cache(maxsize=8192)
def node_prefix(t):
    if t[0] == "HOLE":
        return b"\x01" + name(t[1]) + name(t[2])
    if t[0] != "NODE":
        raise ValueError("definitions must contain expanded NODEs and typed HOLEs")
    return b"\x00" + name(t[1]) + name(t[2]) + t[3] + encode_varint(len(t[4]))


def wire_pattern(t):
    if t[0] == "HOLE":
        return t
    if t[0] != "NODE":
        raise ValueError("definition must be fully expanded")
    # Python considers True and 1 equal. Serialize atoms before interning so
    # sharing can never replace one wire type with another.
    return ("NODE", t[1], t[2], value(t[3]), tuple(wire_pattern(c) for c in t[4]))


def nodes(t):
    yield t
    if t[0] == "NODE":
        for child in t[4]:
            yield from nodes(child)


@lru_cache(maxsize=8192)
def holes(t):
    return tuple((n[1], n[2]) for n in nodes(t) if n[0] == "HOLE")


def arguments(p, t, matches):
    if p[0] == "HOLE":
        if p[1] != t[1] or (t[0] == "HOLE" and p[2] != t[2]):
            return False
        matches.append(t)
        return True
    return (t[0] == "NODE" and p[:4] == t[:4] and len(p[4]) == len(t[4])
            and all(arguments(a, b, matches) for a, b in zip(p[4], t[4])))


def library_with(defs, scaffolds, shared):
    emitted = {}
    prior = defaultdict(list)
    stats = Counter()

    def compile_tree(t):
        if t in emitted:
            return b"\x02" + encode_varint(emitted[t]), Counter(scaffold_refs=1)
        if t[0] == "HOLE":
            return node_prefix(t), Counter()
        items = [compile_tree(c) for c in t[4]]
        cost = node_prefix(t) + b"".join(b for b, _ in items)
        counts = sum((s for _, s in items), Counter())
        for i, pat in prior[t[:4]]:
            args = []
            if not arguments(pat, t, args):
                continue
            nested = [compile_tree(a) for a in args]
            use = b"\x03" + encode_varint(i) + b"".join(b for b, _ in nested)
            if len(use) < len(cost):
                cost = use
                counts = sum((s for _, s in nested), Counter(earlier_template_calls=1))
                counts["forwarded_holes"] += sum(a[0] == "HOLE" for a in args)
                counts["concrete_arguments"] += sum(a[0] == "NODE" for a in args)
        return cost, counts

    out = bytearray(b"SL1" + bytes([int(shared)]) + encode_varint(len(defs)) + encode_varint(len(scaffolds)))
    for i, t in enumerate(scaffolds):
        part, count = compile_tree(t)
        out.extend(part)
        stats.update(count)
        emitted[t] = i
    for i, t in enumerate(defs):
        if t[0] != "NODE":
            raise ValueError("a definition root must be a NODE")
        part, count = compile_tree(t)
        out.extend(part)
        stats.update(count)
        if shared:
            prior[t[:4]].append((i, t))
    for key in ("scaffold_refs", "earlier_template_calls", "forwarded_holes", "concrete_arguments"):
        stats.setdefault(key, 0)
    stats["scaffold_nodes"] = len(scaffolds)
    return bytes(out), dict(stats)


@lru_cache(maxsize=128)
def _library(defs, fmt):
    if fmt not in ("flat", "dag"):
        raise ValueError("library format must be flat or dag")
    best = library_with(defs, (), fmt == "dag")
    if fmt == "flat":
        return best
    # Purchase a scaffold only if the complete library gets shorter. Ordering is
    # deterministic; an existing earlier-template application wins equal costs.
    occurrences = Counter(t for root in defs for t in set(nodes(root)) if t[0] == "NODE")
    candidates = [(t, sum(1 for _ in nodes(t))) for t, n in occurrences.items() if n >= 2]
    candidates.sort(key=lambda c: (c[1], repr(c[0])))
    purchased = []
    for t, _ in candidates:
        trial = library_with(defs, (*purchased, t), True)
        if len(trial[0]) < len(best[0]):
            purchased.append(t)
            best = trial
    return best


def encode_library(definitions, format):
    return _library(tuple(map(wire_pattern, definitions)), format)[0]


def library_stats(definitions, format):
    return dict(_library(tuple(map(wire_pattern, definitions)), format)[1])


def label(t):
    return (t[0] == "CALL", t[2])


def events(docs, defs):
    def walk(t, where):
        yield t, where
        if t[0] == "NODE":
            for c in t[4]:
                yield from walk(c, None)
        elif t[0] == "CALL":
            _, group, fid, shift, args = t
            if fid not in range(len(defs)) or defs[fid][1] != group or shift not in range(8):
                raise ValueError("invalid template id, group, or register shift")
            signature = holes(defs[fid])
            if len(args) != len(signature):
                raise ValueError("call argument count mismatch")
            for i, (child, (child_group, _)) in enumerate(zip(args, signature)):
                if child[1] != child_group:
                    raise ValueError("typed hole mismatch")
                yield from walk(child, (fid, i))
        else:
            raise ValueError("payload requires NODE or CALL")
    for doc in docs:
        if not isinstance(doc, bytes):
            for t in doc:
                yield from walk(t, None)


@dataclass
class Model:
    blob: bytes
    labels: dict
    tables: dict


def fit_prior(training_docs, definitions, prior):
    """Fit a typed general dispatch table and optional immediate call-hole tables."""
    if prior not in ("general", "hole"):
        raise ValueError("prior must be general or hole")
    defs = tuple(definitions)
    base, local = defaultdict(Counter), defaultdict(Counter)
    for t, where in events(training_docs, defs):
        base[t[1]][label(t)] += 1
        if where is not None and prior == "hole":
            local[(t[1], *where)][label(t)] += 1
    labels, tables, rows, holes_rows = {}, {}, [], []
    for group, counts in sorted(base.items()):
        alphabet = sorted(counts)
        labels[group] = {s:i+1 for i,s in enumerate(alphabet)}
        weights = quantize_weights([1, *(counts[s]+1 for s in alphabet)])
        rows.append([group, alphabet, weights])
        tables[(group,)] = build_cum(weights)
    for (group, fid, ordinal), counts in sorted(local.items()):
        if sum(counts.values()) < 2:
            continue
        # Sixteen pseudo-observations from the general distribution + one
        # per symbol. Unseen holes and unknown groups always use shared backoff.
        bg = tables[(group,)]
        bw = [b-a for a,b in zip(bg,bg[1:])]
        w = [1 + 16*n//bg[-1] for n in bw]
        for symbol, n in counts.items():
            w[labels[group][symbol]] += n
        w = quantize_weights(w)
        holes_rows.append([group, fid, ordinal, w])
        tables[(group,fid,ordinal)] = build_cum(w)
    data = json.dumps([rows,holes_rows], ensure_ascii=False, separators=(",",":")).encode()
    return Model(bytes([int(prior == "hole")]) + zlib.compress(data, 9), labels, tables)


def encode_payload(documents, definitions, model):
    docs, defs = tuple(documents), tuple(definitions)
    side = bytearray(encode_varint(len(docs)))
    for doc in docs:
        if isinstance(doc, bytes):
            side.extend(b"\x01" + block(doc))
        else:
            side.extend(b"\x00" + encode_varint(len(doc)))
    enc = ArithmeticEncoder()
    for t, where in events(docs, defs):
        group = t[1]
        side.extend(name(group))
        idx = model.labels.get(group, {}).get(label(t), 0)
        cum = model.tables.get((group,*where), model.tables.get((group,))) if where else model.tables.get((group,))
        if cum is not None:
            enc.encode(cum, idx)
        if idx == 0:
            side.append(int(t[0]=="CALL"))
            side.extend(encode_varint(t[2]) if t[0]=="CALL" else name(t[2]))
        if t[0]=="NODE":
            side.extend(value(t[3]))
            side.extend(encode_varint(len(t[4])))
        else:
            side.append(t[3])
    return block(zlib.compress(bytes(side), 6)) + enc.finish()


def encode_archive(documents, definitions, format, model):
    defs = tuple(definitions)
    lib = encode_library(defs, format)
    payload = encode_payload(documents, defs, model)
    header = b"SDA1" + block(lib) + block(model.blob)
    data = header + block(payload)
    data += struct.pack(">I", zlib.crc32(data))
    framing = len(data)-len(lib)-len(model.blob)-len(payload)
    return data, dict(library_bytes=len(lib), model_bytes=len(model.blob),
                      header_bytes=len(header), framing_bytes=framing, payload_bytes=len(payload),
                      payload_framing_bytes=len(data)-len(header)-len(payload),
                      complete_bytes=len(data))
