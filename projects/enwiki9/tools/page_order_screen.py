#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import pathlib
import re

PAGE_OPEN = b"  <page>\n"
PAGE_CLOSE = b"  </page>\n"


def field(page: bytes, pat: bytes) -> bytes:
    m = re.search(pat, page, re.S | re.I)
    return m.group(1) if m else b""


def norm(v: bytes, limit: int = 240) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", v.lower()).strip()[:limit]


def revnorm(v: bytes, limit: int = 120) -> bytes:
    parts = norm(v, limit).split()
    return b" ".join(reversed(parts))


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
    ids = [int(field(page, rb"<id>(\d+)</id>") or 10**30) for page in pages]
    return data[:first], pages, data[pos:], ids


def bucket(n: int) -> int:
    out = 0
    while n > 15 and out < 31:
        n >>= 1
        out += 1
    return out


def title(page: bytes) -> bytes:
    return field(page, rb"<title>(.*?)</title>")


def base_parts(page: bytes) -> tuple[bytes, bytes, list[bytes], bytes, bytes]:
    t = title(page)
    redirect = field(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
    cats = re.findall(rb"\[\[Category:([^\]\|\n]{1,100})", page, re.I)
    infobox = field(page, rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
    template = field(page, rb"\{\{([^\|\}\n]{1,80})")
    return t, redirect, cats, infobox, template


def key(mode: str, page: bytes, pid: int) -> tuple:
    t, redirect, cats, infobox, template = base_parts(page)
    nt = norm(t)
    if mode == "original":
        return (pid,)
    if mode == "geometry":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (norm(b"c " + b" ".join(sorted(cats)) + b" t " + t[:40]), pid)
        if infobox:
            return (norm(b"i " + infobox), pid)
        return (norm(b"x " + (template or t)), pid)
    if mode == "geometry_title":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (norm(b"c " + b" ".join(sorted(cats)) + b" t " + t[:80]), pid)
        if infobox:
            return (norm(b"i " + infobox + b" t " + t), pid)
        return (norm(b"x " + (template or t) + b" t " + t), pid)
    if mode == "geometry_suffix":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (norm(b"c " + b" ".join(sorted(cats)) + b" s " + t[-30:]), pid)
        if infobox:
            return (norm(b"i " + infobox + b" s " + t[-30:]), pid)
        return (norm(b"x " + (template or t) + b" s " + t[-30:]), pid)
    if mode == "geometry_catonly":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (norm(b"c " + b" ".join(sorted(cats))), pid)
        if infobox:
            return (norm(b"i " + infobox), pid)
        return (norm(b"x " + (template or t)), pid)
    if mode == "geometry_cat_title_suffix":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (
                norm(b"c " + b" ".join(sorted(cats)) + b" t " + t[:48] + b" s " + t[-32:]),
                pid,
            )
        if infobox:
            return (norm(b"i " + infobox + b" t " + t[:48] + b" s " + t[-32:]), pid)
        return (norm(b"x " + (template or t) + b" t " + t[:48] + b" s " + t[-32:]), pid)
    if mode == "geometry_revtitle":
        if redirect:
            return (norm(b"z " + redirect), pid)
        if cats:
            return (norm(b"c " + b" ".join(sorted(cats))), revnorm(t), pid)
        if infobox:
            return (norm(b"i " + infobox), revnorm(t), pid)
        return (norm(b"x " + (template or t)), revnorm(t), pid)
    if mode == "geometry_title_bucket":
        head = nt[:1]
        if redirect:
            return (head, norm(b"z " + redirect), pid)
        if cats:
            return (head, norm(b"c " + b" ".join(sorted(cats)) + b" t " + t[:60]), pid)
        if infobox:
            return (head, norm(b"i " + infobox + b" t " + t[:60]), pid)
        return (head, norm(b"x " + (template or t) + b" t " + t[:60]), pid)
    if mode == "geometry_size":
        if redirect:
            return (norm(b"z " + redirect), bucket(len(page)), pid)
        if cats:
            return (
                norm(b"c " + b" ".join(sorted(cats)) + b" t " + t[:40]),
                bucket(len(page)),
                pid,
            )
        if infobox:
            return (norm(b"i " + infobox), bucket(len(page)), pid)
        return (norm(b"x " + (template or t)), bucket(len(page)), pid)
    if mode == "geometry_ns":
        ns = nt.split(b" ", 1)[0] if b" " in nt else b""
        if redirect:
            return (b"z", norm(redirect), pid)
        if nt.startswith(b"category "):
            return (b"c0", nt, pid)
        if cats:
            return (b"c1", norm(b" ".join(sorted(cats))), nt[:80], pid)
        if infobox:
            return (b"i", norm(infobox), nt[:80], pid)
        return (b"x", norm(template or t), ns, nt[:80], pid)
    raise ValueError(mode)


def reorder(data: bytes, mode: str) -> tuple[bytes, dict]:
    head, pages, tail, ids = split_pages(data)
    if not pages:
        return data, {"pages": 0, "roundtrip": True}
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate page ids")
    order = sorted(range(len(pages)), key=lambda i: key(mode, pages[i], ids[i]))
    ordered = head + b"".join(pages[i] for i in order) + tail
    restored = head + b"".join(pages[i] for i in sorted(order, key=lambda i: ids[i])) + tail
    return ordered, {
        "pages": len(pages),
        "head": len(head),
        "tail": len(tail),
        "roundtrip": restored == data,
        "ordered_sha256": hashlib.sha256(ordered).hexdigest(),
    }


def xz_size(data: bytes) -> int:
    return len(lzma.compress(data, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data/enwik9"))
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--raw-out-dir", type=pathlib.Path)
    ap.add_argument(
        "--modes",
        nargs="+",
        default=[
            "original",
            "geometry",
            "geometry_title",
            "geometry_suffix",
            "geometry_catonly",
            "geometry_cat_title_suffix",
            "geometry_revtitle",
            "geometry_title_bucket",
            "geometry_size",
            "geometry_ns",
        ],
    )
    args = ap.parse_args()

    data = args.data.read_bytes()[: args.limit]
    rows = []
    for mode in args.modes:
        ordered, stats = reorder(data, mode)
        if not stats["roundtrip"]:
            raise SystemExit(f"{mode}: restore check failed")
        if args.raw_out_dir:
            args.raw_out_dir.mkdir(parents=True, exist_ok=True)
            (args.raw_out_dir / f"{args.limit}_{mode}.raw").write_bytes(ordered)
        rows.append({"mode": mode, "xz_bytes": xz_size(ordered), **stats})
    base = next((row for row in rows if row["mode"] == "geometry"), rows[0])
    original = next((row for row in rows if row["mode"] == "original"), None)
    original_xz = original["xz_bytes"] if original else xz_size(data)
    for row in rows:
        row["delta_vs_geometry"] = row["xz_bytes"] - base["xz_bytes"]
        row["delta_vs_original"] = row["xz_bytes"] - original_xz
    result = {
        "input_bytes": len(data),
        "codec": "Python lzma FORMAT_XZ preset=9|PRESET_EXTREME over reordered raw XML",
        "rows": rows,
        "best_mode": min(rows, key=lambda row: row["xz_bytes"])["mode"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
