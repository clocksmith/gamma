#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import subprocess
import tempfile


PAGE_OPEN = b"  <page>\n"
PAGE_CLOSE = b"  </page>\n"


def norm(v: bytes, limit: int = 120) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", v.lower()).strip()[:limit]


def field(page: bytes, pat: bytes) -> bytes:
    m = re.search(pat, page, re.S | re.I)
    return m.group(1) if m else b""


def page_id(page: bytes, fallback: int) -> int:
    m = re.search(rb"<id>(\d+)</id>", page)
    return int(m.group(1)) if m else 10**18 + fallback


def split_pages(data: bytes) -> tuple[bytes, list[bytes], bytes, list[int]]:
    first = data.find(PAGE_OPEN)
    if first < 0:
        return data, [], b"", []
    pages: list[bytes] = []
    pos = first
    while True:
        start = data.find(PAGE_OPEN, pos)
        if start < 0:
            break
        end = data.find(PAGE_CLOSE, start)
        if end < 0:
            break
        end += len(PAGE_CLOSE)
        pages.append(data[start:end])
        pos = end
    return data[:first], pages, data[pos:], [page_id(p, i) for i, p in enumerate(pages)]


def first_template(page: bytes) -> bytes:
    return norm(field(page, rb"\{\{([^\|\}\n]{1,96})"), 96)


def first_category(page: bytes) -> bytes:
    return norm(field(page, rb"\[\[Category:([^\]\|\n]{1,96})"), 96)


def title(page: bytes) -> bytes:
    return norm(field(page, rb"<title>(.*?)</title>"), 160)


def page_kind(page: bytes) -> int:
    t = title(page)
    lower = page[:4096].lower()
    if b"#redirect" in lower:
        return 1
    if t.startswith(b"category "):
        return 2
    if t.startswith(b"list of"):
        return 3
    if b"disambiguation" in t:
        return 4
    if b"{{infobox" in lower or b"{{taxobox" in lower:
        return 5
    return 0


def bucket(v: int) -> int:
    b = 0
    while v > 15 and b < 31:
        v >>= 1
        b += 1
    return b


def shape_sig(page: bytes) -> bytes:
    sig = bytearray()
    for raw in page.splitlines()[:160]:
        line = raw.strip()
        if not line:
            sig.append(ord("_"))
        elif line.startswith(b"<"):
            m = re.match(rb"</?([a-zA-Z0-9:_-]+)", line)
            sig.extend((m.group(1).lower()[:8] if m else b"<") + b";")
        elif line.startswith(b"{{"):
            sig.extend(b"T" + first_template(line)[:12] + b";")
        elif line.startswith(b"|"):
            sig.extend(b"P;")
        elif line.startswith(b"=="):
            sig.extend(b"H;")
        elif line.startswith((b"*", b"#", b":", b";")):
            sig.extend(line[:1] + b";")
        else:
            sig.extend(b"W;")
    return hashlib.blake2s(bytes(sig), digest_size=8).digest()


def word_tokens(page: bytes, limit: int = 512) -> list[bytes]:
    text = field(page, rb"<text[^>]*>(.*?)</text>") or page
    tokens: list[bytes] = []
    seen: set[bytes] = set()
    for m in re.finditer(rb"[a-z][a-z0-9]{2,24}", text.lower()):
        w = m.group(0)
        if w in seen:
            continue
        seen.add(w)
        tokens.append(w)
        if len(tokens) >= limit:
            break
    return tokens


def minhash_sig(page: bytes, bands: int = 6) -> tuple[int, ...]:
    tokens = word_tokens(page)
    if not tokens:
        return (0,) * bands
    out: list[int] = []
    for band in range(bands):
        seed = band.to_bytes(1, "little")
        best = (1 << 64) - 1
        for token in tokens:
            h = int.from_bytes(
                hashlib.blake2s(seed + token, digest_size=8).digest(), "little"
            )
            if h < best:
                best = h
        out.append(best >> 40)
    return tuple(out)


def key_for(mode: str, page: bytes, pid: int) -> tuple:
    t = title(page)
    tmpl = first_template(page)
    cat = first_category(page)
    first_link = norm(field(page, rb"\[([^\]\|\n]{1,96})(?:\|[^\]\n]*)?\]"), 96)
    topic_key = cat or tmpl or first_link or t
    size_b = bucket(len(page))
    lines_b = bucket(page.count(b"\n"))
    kind = page_kind(page)
    if mode == "original":
        return (pid,)
    if mode == "title":
        return (t, pid)
    if mode == "topic":
        return (cat or tmpl or t, pid)
    if mode == "topic_shape":
        return (topic_key, shape_sig(page), kind, size_b, lines_b, pid)
    if mode == "topic_minhash":
        return (topic_key, minhash_sig(page, 3), kind, size_b, pid)
    if mode == "topic_shape_minhash":
        return (topic_key, shape_sig(page), minhash_sig(page, 2), kind, size_b, pid)
    if mode == "shape":
        return (shape_sig(page), kind, size_b, lines_b, pid)
    if mode == "family":
        return (kind, tmpl, cat, t[:16], size_b, lines_b, pid)
    if mode == "entity":
        return (topic_key, kind, size_b, pid)
    if mode == "minhash":
        return (minhash_sig(page), kind, size_b, pid)
    raise ValueError(f"unknown mode: {mode}")


def reorder(data: bytes, mode: str) -> tuple[bytes, dict]:
    head, pages, tail, ids = split_pages(data)
    if not pages:
        return data, {"pages": 0, "tail": len(tail), "roundtrip": True}
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate page ids in slice")
    order = sorted(range(len(pages)), key=lambda i: key_for(mode, pages[i], ids[i]))
    out = head + b"".join(pages[i] for i in order) + tail
    restored = head + b"".join(pages[i] for i in sorted(order, key=lambda i: ids[i])) + tail
    return out, {
        "pages": len(pages),
        "head": len(head),
        "tail": len(tail),
        "roundtrip": restored == data,
        "first_ids": [ids[i] for i in order[:8]],
    }


def run_phda9(tool: pathlib.Path, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        src = root / "in"
        dst = root / "out"
        src.write_bytes(data)
        subprocess.run(
            [str(tool), "encode", str(src), str(dst)],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return dst.read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data/enwik9"))
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument(
        "--mode",
        choices=[
            "original",
            "title",
            "topic",
            "topic_shape",
            "topic_minhash",
            "topic_shape_minhash",
            "shape",
            "family",
            "entity",
            "minhash",
        ],
        required=True,
    )
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--raw-out", type=pathlib.Path)
    ap.add_argument("--phda9-tool", type=pathlib.Path, default=pathlib.Path("tools/phda9_wit_tool"))
    args = ap.parse_args()

    data = args.data.read_bytes()[: args.limit]
    ordered, stats = reorder(data, args.mode)
    if not stats["roundtrip"]:
        raise SystemExit(f"{args.mode}: reorder restore check failed")
    if args.raw_out:
        args.raw_out.write_bytes(ordered)
    result = {
        "mode": args.mode,
        "input": len(data),
        "ordered": len(ordered),
        **stats,
    }
    if args.out:
        ph = run_phda9(args.phda9_tool.resolve(), ordered)
        args.out.write_bytes(ph)
        result["phda9"] = len(ph)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
