#!/usr/bin/env python3
"""Monte Carlo search for blockwise enwiki9 compression strategy mixes.

The search space is a portfolio compressor: each recipe selects a block size
and a small set of reversible candidate coders. For every block, the encoder
tries the recipe's candidates and stores the index of the smallest payload.
The decoder follows the stored candidate index and reconstructs the bytes.

This is an experimental-screening tool, not a contest submission wrapper, and
not the primary FX2-SC raw-stream sidecar lane from FX2_SC.md. Its transforms
physically rewrite, split, or wrap payloads, so results belong in the custom
backend/rate-ledger/destructive-transform control set unless a candidate is
later converted into a recomputable sidecar context.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import pathlib
import random
import re
import sys
import time
import zlib
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "monte_carlo_strategy_search"

MAGIC = b"MCS1"
ESC = 0
ESC_ZERO = 0
ESC_TOKEN_BASE = 1
ESC_WORD_BASE = 128

WORD_RE = re.compile(rb"[A-Za-z][A-Za-z_]{3,31}")

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
    b"[[File:",
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
    b"|url=",
    b"|title=",
    b"|date=",
    b"|accessdate=",
    b"|publisher=",
    b"|author=",
    b"|first=",
    b"|last=",
    b"== External links ==",
    b"== References ==",
    b"== See also ==",
    b"{{cite web",
    b"{{cite book",
    b"{{main",
    b"{{IPA",
    b"{{flagicon",
    b"{{note",
    b"{{ref",
    b"{{succession box",
    b"align=",
    b"style=",
    b"class=",
    b"rowspan=",
    b"colspan=",
]
TOKENS = sorted(TOKENS, key=lambda x: (-len(x), x))

FIELD_PAIRS = [
    (b'<text xml:space="preserve">', b"</text>", "text"),
    (b"<title>", b"</title>", "title"),
    (b"<comment>", b"</comment>", "comment"),
    (b"<username>", b"</username>", "username"),
    (b"<timestamp>", b"</timestamp>", "timestamp"),
    (b"<id>", b"</id>", "id"),
    (b"<ip>", b"</ip>", "ip"),
]


def uvar(n: int) -> bytes:
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def ruvar(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        b = buf[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def pack_parts(parts: Iterable[bytes]) -> bytes:
    parts = list(parts)
    out = bytearray()
    for part in parts:
        out.extend(uvar(len(part)))
    for part in parts:
        out.extend(part)
    return bytes(out)


def unpack_parts(buf: bytes, count: int, pos: int = 0) -> tuple[list[bytes], int]:
    sizes = []
    for _ in range(count):
        size, pos = ruvar(buf, pos)
        sizes.append(size)
    parts = []
    for size in sizes:
        parts.append(buf[pos:pos + size])
        pos += size
    return parts, pos


@dataclass(frozen=True)
class Backend:
    kind: str
    level: int

    def key(self) -> str:
        return f"{self.kind}{self.level}"

    def compress(self, data: bytes) -> bytes:
        if self.kind == "zlib":
            return zlib.compress(data, self.level)
        if self.kind == "bz2":
            return bz2.compress(data, compresslevel=self.level)
        if self.kind == "lzma":
            preset = self.level
            if self.level >= 90:
                preset = (self.level - 90) | lzma.PRESET_EXTREME
            return lzma.compress(data, preset=preset)
        raise ValueError(f"unknown backend: {self.kind}")

    def decompress(self, data: bytes) -> bytes:
        if self.kind == "zlib":
            return zlib.decompress(data)
        if self.kind == "bz2":
            return bz2.decompress(data)
        if self.kind == "lzma":
            return lzma.decompress(data)
        raise ValueError(f"unknown backend: {self.kind}")

    def to_json(self) -> dict:
        return {"kind": self.kind, "level": self.level}

    @staticmethod
    def from_json(obj: dict) -> "Backend":
        return Backend(str(obj["kind"]), int(obj["level"]))


@dataclass(frozen=True)
class Candidate:
    transform: str
    backend: Backend
    token_count: int = 0
    word_count: int = 0
    min_word: int = 5

    def key(self) -> str:
        if self.transform == "tokens":
            return f"tok{self.token_count}:{self.backend.key()}"
        if self.transform == "wordmap":
            return f"word{self.word_count}m{self.min_word}:{self.backend.key()}"
        return f"{self.transform}:{self.backend.key()}"

    def compress(self, data: bytes) -> bytes:
        if self.transform == "raw":
            return self.backend.compress(data)
        if self.transform == "tokens":
            return self.backend.compress(token_encode(data, self.token_count))
        if self.transform == "wordmap":
            return self.backend.compress(
                wordmap_encode(data, self.word_count, self.min_word)
            )
        if self.transform == "field_demux":
            skeleton, fields, tail = field_split(data)
            cskel = self.backend.compress(skeleton)
            cfields = self.backend.compress(fields)
            ctail = self.backend.compress(tail)
            return pack_parts([cskel, cfields, ctail])
        raise ValueError(f"unknown transform: {self.transform}")

    def decompress(self, payload: bytes) -> bytes:
        if self.transform == "raw":
            return self.backend.decompress(payload)
        if self.transform == "tokens":
            return token_decode(self.backend.decompress(payload), self.token_count)
        if self.transform == "wordmap":
            return wordmap_decode(self.backend.decompress(payload))
        if self.transform == "field_demux":
            parts, pos = unpack_parts(payload, 3)
            if pos != len(payload):
                raise ValueError("field_demux trailing bytes")
            skeleton = self.backend.decompress(parts[0])
            fields = self.backend.decompress(parts[1])
            tail = self.backend.decompress(parts[2])
            return field_join(skeleton, fields, tail)
        raise ValueError(f"unknown transform: {self.transform}")

    def to_json(self) -> dict:
        return {
            "transform": self.transform,
            "backend": self.backend.to_json(),
            "token_count": self.token_count,
            "word_count": self.word_count,
            "min_word": self.min_word,
        }

    @staticmethod
    def from_json(obj: dict) -> "Candidate":
        return Candidate(
            transform=str(obj["transform"]),
            backend=Backend.from_json(obj["backend"]),
            token_count=int(obj.get("token_count", 0)),
            word_count=int(obj.get("word_count", 0)),
            min_word=int(obj.get("min_word", 5)),
        )


@dataclass(frozen=True)
class Recipe:
    block_size: int
    candidates: tuple[Candidate, ...]

    def key(self) -> str:
        body = "|".join(c.key() for c in self.candidates)
        return f"blk{self.block_size}:{body}"

    def to_json(self) -> dict:
        return {
            "block_size": self.block_size,
            "candidates": [c.to_json() for c in self.candidates],
        }

    @staticmethod
    def from_json(obj: dict) -> "Recipe":
        return Recipe(
            block_size=int(obj["block_size"]),
            candidates=tuple(Candidate.from_json(c) for c in obj["candidates"]),
        )


def token_encode(data: bytes, token_count: int) -> bytes:
    tokens = TOKENS[:token_count]
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == ESC:
            out.extend((ESC, ESC_ZERO))
            i += 1
            continue
        matched = False
        for idx, tok in enumerate(tokens, ESC_TOKEN_BASE):
            if data.startswith(tok, i):
                out.extend((ESC, idx))
                i += len(tok)
                matched = True
                break
        if not matched:
            out.append(b)
            i += 1
    return bytes(out)


def token_decode(data: bytes, token_count: int) -> bytes:
    tokens = TOKENS[:token_count]
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        i += 1
        if b != ESC:
            out.append(b)
            continue
        if i >= len(data):
            raise ValueError("trailing token escape")
        code = data[i]
        i += 1
        if code == ESC_ZERO:
            out.append(ESC)
            continue
        idx = code - ESC_TOKEN_BASE
        if idx < 0 or idx >= len(tokens):
            raise ValueError("bad token code")
        out.extend(tokens[idx])
    return bytes(out)


def choose_words(data: bytes, word_count: int, min_word: int) -> list[bytes]:
    counts: Counter[bytes] = Counter()
    for match in WORD_RE.finditer(data):
        word = match.group(0)
        if len(word) >= min_word:
            counts[word] += 1
    scored = []
    for word, count in counts.items():
        gain = count * (len(word) - 2) - len(word) - 2
        if gain > 0:
            scored.append((gain, count, len(word), word))
    scored.sort(reverse=True)
    limit = min(word_count, 127)
    return [word for _, _, _, word in scored[:limit]]


def wordmap_encode(data: bytes, word_count: int, min_word: int) -> bytes:
    words = choose_words(data, word_count, min_word)
    out = bytearray(b"WM1")
    out.extend(uvar(len(words)))
    for word in words:
        out.extend(uvar(len(word)))
        out.extend(word)
    if not words:
        out.extend(escape_high_bytes(data))
        return bytes(out)
    code_for = {word: bytes([ESC, ESC_WORD_BASE + i]) for i, word in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    pos = 0
    for match in pat.finditer(data):
        out.extend(escape_high_bytes(data[pos:match.start()]))
        out.extend(code_for[match.group(0)])
        pos = match.end()
    out.extend(escape_high_bytes(data[pos:]))
    return bytes(out)


def escape_high_bytes(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == ESC or b >= ESC_WORD_BASE:
            out.extend((ESC, b))
        else:
            out.append(b)
    return bytes(out)


def wordmap_decode(data: bytes) -> bytes:
    if not data.startswith(b"WM1"):
        raise ValueError("bad wordmap")
    pos = 3
    nwords, pos = ruvar(data, pos)
    words = []
    for _ in range(nwords):
        size, pos = ruvar(data, pos)
        words.append(data[pos:pos + size])
        pos += size
    out = bytearray()
    while pos < len(data):
        b = data[pos]
        pos += 1
        if b != ESC:
            out.append(b)
            continue
        if pos >= len(data):
            raise ValueError("trailing word escape")
        code = data[pos]
        pos += 1
        if code >= ESC_WORD_BASE:
            idx = code - ESC_WORD_BASE
            if idx >= len(words):
                raise ValueError("bad word code")
            out.extend(words[idx])
        else:
            out.append(code)
    return bytes(out)


def put_skeleton(out: bytearray, b: int) -> None:
    if b == ESC:
        out.extend((ESC, ESC_ZERO))
    else:
        out.append(b)


def field_split(data: bytes) -> tuple[bytes, bytes, bytes]:
    skeleton = bytearray()
    fields = bytearray()
    tail = bytearray()
    pos = 0
    n = len(data)
    while pos < n:
        matched = False
        for field_id, (open_tag, close_tag, _) in enumerate(FIELD_PAIRS, 1):
            if not data.startswith(open_tag, pos):
                continue
            start = pos + len(open_tag)
            end = data.find(close_tag, start)
            if end < 0:
                continue
            for b in open_tag:
                put_skeleton(skeleton, b)
            body = data[start:end]
            skeleton.extend((ESC, field_id))
            skeleton.extend(uvar(len(body)))
            fields.extend(body)
            for b in close_tag:
                put_skeleton(skeleton, b)
            pos = end + len(close_tag)
            matched = True
            break
        if matched:
            continue
        b = data[pos]
        if b in (ord("{"), ord("["), ord("|"), ord("="), ord("<"), ord(">")):
            tail.append(b)
        put_skeleton(skeleton, b)
        pos += 1
    return bytes(skeleton), bytes(fields), bytes(tail)


def field_join(skeleton: bytes, fields: bytes, tail: bytes) -> bytes:
    del tail
    out = bytearray()
    field_pos = 0
    pos = 0
    while pos < len(skeleton):
        b = skeleton[pos]
        pos += 1
        if b != ESC:
            out.append(b)
            continue
        if pos >= len(skeleton):
            raise ValueError("trailing field escape")
        code = skeleton[pos]
        pos += 1
        if code == ESC_ZERO:
            out.append(ESC)
            continue
        if not 1 <= code <= len(FIELD_PAIRS):
            raise ValueError("bad field code")
        size, pos = ruvar(skeleton, pos)
        out.extend(fields[field_pos:field_pos + size])
        field_pos += size
    if field_pos != len(fields):
        raise ValueError("unused field payload")
    return bytes(out)


def pack_archive(data: bytes, recipe: Recipe) -> tuple[bytes, dict]:
    recipe_blob = json.dumps(recipe.to_json(), sort_keys=True, separators=(",", ":")).encode()
    out = bytearray(MAGIC)
    out.extend(uvar(len(data)))
    out.extend(uvar(len(recipe_blob)))
    out.extend(recipe_blob)
    counts: Counter[str] = Counter()
    blocks = 0
    candidate_bytes: Counter[str] = Counter()
    for start in range(0, len(data), recipe.block_size):
        block = data[start:start + recipe.block_size]
        choices = []
        for idx, candidate in enumerate(recipe.candidates):
            payload = candidate.compress(block)
            choices.append((len(payload), idx, candidate, payload))
        _, idx, candidate, payload = min(choices, key=lambda x: (x[0], x[1]))
        out.extend(uvar(idx))
        out.extend(uvar(len(payload)))
        out.extend(payload)
        counts[candidate.key()] += 1
        candidate_bytes[candidate.key()] += len(payload)
        blocks += 1
    stats = {
        "blocks": blocks,
        "choice_counts": dict(counts),
        "choice_payload_bytes": dict(candidate_bytes),
        "recipe_header_bytes": len(MAGIC) + len(uvar(len(data))) + len(uvar(len(recipe_blob))) + len(recipe_blob),
    }
    return bytes(out), stats


def unpack_archive(archive: bytes) -> bytes:
    if not archive.startswith(MAGIC):
        raise ValueError("bad archive magic")
    pos = len(MAGIC)
    raw_size, pos = ruvar(archive, pos)
    recipe_size, pos = ruvar(archive, pos)
    recipe = Recipe.from_json(json.loads(archive[pos:pos + recipe_size]))
    pos += recipe_size
    out = bytearray()
    while pos < len(archive):
        idx, pos = ruvar(archive, pos)
        size, pos = ruvar(archive, pos)
        payload = archive[pos:pos + size]
        pos += size
        out.extend(recipe.candidates[idx].decompress(payload))
    if len(out) != raw_size:
        raise ValueError(f"size mismatch: got {len(out)}, expected {raw_size}")
    return bytes(out)


def recipe_digest(recipe: Recipe) -> str:
    return hashlib.sha256(recipe.key().encode()).hexdigest()[:12]


def candidate_pool(rng: random.Random) -> list[Candidate]:
    backends = [
        Backend("zlib", 6),
        Backend("zlib", 9),
        Backend("bz2", 9),
        Backend("lzma", 6),
        Backend("lzma", 99),
    ]
    pool = [Candidate("raw", b) for b in backends]
    for token_count in (16, 32, 48, 64):
        for backend in backends:
            pool.append(Candidate("tokens", backend, token_count=token_count))
    for word_count in (24, 48, 96):
        for min_word in (5, 7, 9):
            for backend in backends:
                pool.append(
                    Candidate(
                        "wordmap",
                        backend,
                        word_count=word_count,
                        min_word=min_word,
                    )
                )
    for backend in backends:
        pool.append(Candidate("field_demux", backend))
    rng.shuffle(pool)
    return pool


def baseline_recipes() -> list[Recipe]:
    return [
        Recipe(1 << 30, (Candidate("raw", Backend("lzma", 99)),)),
        Recipe(4 << 20, (Candidate("raw", Backend("lzma", 99)),)),
        Recipe(
            4 << 20,
            (
                Candidate("raw", Backend("lzma", 99)),
                Candidate("tokens", Backend("lzma", 99), token_count=64),
                Candidate("field_demux", Backend("lzma", 99)),
            ),
        ),
    ]


def random_recipe(rng: random.Random) -> Recipe:
    block_size = rng.choice([512 << 10, 1 << 20, 2 << 20, 4 << 20, 8 << 20])
    pool = candidate_pool(rng)
    forced = [
        Candidate("raw", Backend("lzma", 99)),
        Candidate("raw", Backend("zlib", 9)),
    ]
    width = rng.randint(3, 8)
    chosen = []
    seen = set()
    for candidate in forced + pool:
        key = candidate.key()
        if key in seen:
            continue
        chosen.append(candidate)
        seen.add(key)
        if len(chosen) >= width:
            break
    return Recipe(block_size, tuple(chosen))


def evaluate(data: bytes, recipe: Recipe, scope: int, phase: str, trial: int) -> dict:
    started = time.perf_counter()
    archive, stats = pack_archive(data, recipe)
    packed_s = time.perf_counter() - started
    started = time.perf_counter()
    restored = unpack_archive(archive)
    unpacked_s = time.perf_counter() - started
    ok = restored == data
    return {
        "phase": phase,
        "trial": trial,
        "scope": scope,
        "recipe_id": recipe_digest(recipe),
        "recipe": recipe.to_json(),
        "archive_size": len(archive),
        "bits_per_byte": round(len(archive) * 8 / len(data), 6),
        "roundtrip_ok": ok,
        "pack_time_s": round(packed_s, 4),
        "unpack_time_s": round(unpacked_s, 4),
        "stats": stats,
    }


def write_jsonl(path: pathlib.Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def read_scope(data_path: pathlib.Path, scope: int) -> bytes:
    with data_path.open("rb") as fh:
        return fh.read(scope)


def summarize(rows: list[dict], out_dir: pathlib.Path) -> None:
    by_scope: dict[int, list[dict]] = {}
    for row in rows:
        by_scope.setdefault(int(row["scope"]), []).append(row)
    lines = ["# Monte Carlo Strategy Search", ""]
    for scope in sorted(by_scope):
        valid = [r for r in by_scope[scope] if r["roundtrip_ok"]]
        valid.sort(key=lambda r: r["archive_size"])
        lines.append(f"## scope={scope}")
        lines.append("")
        lines.append("| rank | phase | recipe_id | archive_size | b/B | block_size | choices |")
        lines.append("|---:|---|---|---:|---:|---:|---|")
        for rank, row in enumerate(valid[:10], 1):
            choices = ",".join(
                f"{k}:{v}" for k, v in sorted(row["stats"]["choice_counts"].items())
            )
            lines.append(
                f"| {rank} | {row['phase']} | {row['recipe_id']} | "
                f"{row['archive_size']} | {row['bits_per_byte']} | "
                f"{row['recipe']['block_size']} | `{choices}` |"
            )
        lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=923)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--promote", type=int, default=6)
    parser.add_argument("--scopes", type=int, nargs="+", default=[10_000_000, 100_000_000])
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"data missing: {args.data}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.out_dir / "runs.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()

    rng = random.Random(args.seed)
    recipes: list[Recipe] = baseline_recipes()
    seen = {r.key() for r in recipes}
    while len(recipes) < args.samples + len(baseline_recipes()):
        recipe = random_recipe(rng)
        if recipe.key() in seen:
            continue
        recipes.append(recipe)
        seen.add(recipe.key())

    all_rows: list[dict] = []
    first_scope = min(args.scopes)
    print(
        f"[monte-carlo] seed={args.seed} recipes={len(recipes)} "
        f"search_scope={first_scope} data={args.data}"
    )
    data = read_scope(args.data, first_scope)
    for trial, recipe in enumerate(recipes):
        row = evaluate(data, recipe, first_scope, "search", trial)
        all_rows.append(row)
        write_jsonl(jsonl_path, row)
        print(
            f"[search] trial={trial} scope={first_scope} "
            f"recipe={row['recipe_id']} archive={row['archive_size']} "
            f"bpb={row['bits_per_byte']} ok={row['roundtrip_ok']}"
        )
        if not row["roundtrip_ok"]:
            return 1

    ranked = sorted(all_rows, key=lambda r: r["archive_size"])
    promoted_recipes = [
        Recipe.from_json(row["recipe"])
        for row in ranked[: max(1, args.promote)]
    ]
    for scope in sorted(s for s in args.scopes if s != first_scope):
        data = read_scope(args.data, scope)
        if len(data) != scope:
            raise SystemExit(f"wanted {scope} bytes, read {len(data)} bytes")
        print(f"[promote] scope={scope} recipes={len(promoted_recipes)}")
        for trial, recipe in enumerate(promoted_recipes):
            row = evaluate(data, recipe, scope, "promote", trial)
            all_rows.append(row)
            write_jsonl(jsonl_path, row)
            print(
                f"[promote] trial={trial} scope={scope} "
                f"recipe={row['recipe_id']} archive={row['archive_size']} "
                f"bpb={row['bits_per_byte']} ok={row['roundtrip_ok']}"
            )
            if not row["roundtrip_ok"]:
                return 1

    summarize(all_rows, args.out_dir)
    best = min(all_rows, key=lambda r: (r["scope"], r["archive_size"]))
    print(
        f"[done] rows={len(all_rows)} best_initial_recipe={best['recipe_id']} "
        f"summary={args.out_dir / 'summary.md'} jsonl={jsonl_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
