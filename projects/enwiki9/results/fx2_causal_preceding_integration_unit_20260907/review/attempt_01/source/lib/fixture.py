"""Deterministic synthetic enwik9-like fixture generator.

The cloud cross-host determinism check needs an input that both hosts can
produce byte-identically without downloading the full 1 GB enwik9. This
generator produces a reproducible synthetic Wikipedia-like XML stream from a
fixed seed.

The output is byte-deterministic given (seed, target_size, schema).

Schema: a sequence of <page>...</page> blocks with realistic XML structure.
The text content uses a small deterministic vocabulary cycled through a
linear congruential PRNG so the byte stream is reproducible across hosts.

Usage:
    python3 lib/fixture.py --size 10000000 --out data/fixture_10mb.bin
"""

from __future__ import annotations

import argparse
import pathlib
import sys

VOCAB = [
    b"the", b"of", b"and", b"to", b"in", b"a", b"is", b"that", b"was", b"for",
    b"as", b"with", b"by", b"on", b"he", b"at", b"from", b"his", b"this",
    b"are", b"or", b"be", b"an", b"were", b"have", b"had", b"not", b"but",
    b"which", b"one", b"all", b"their", b"has", b"more", b"its", b"who",
    b"they", b"been", b"first", b"its", b"when", b"can", b"after", b"two",
    b"new", b"city", b"state", b"war", b"world", b"time", b"year", b"used",
    b"made", b"such", b"also", b"into", b"only", b"some", b"most", b"about",
    b"between", b"under", b"during", b"early", b"later", b"named", b"called",
    b"known", b"over", b"however", b"became", b"these", b"those", b"three",
    b"part", b"area", b"north", b"south", b"east", b"west", b"river",
    b"mountain", b"language", b"culture", b"government", b"church", b"king",
    b"president", b"university", b"system", b"science", b"history",
]

TITLES = [
    b"Anarchism", b"Autism", b"Albedo", b"Achilles", b"Abraham_Lincoln",
    b"Aristotle", b"An_American_in_Paris", b"Academy_Award", b"Apollo_11",
    b"Albert_Einstein", b"Atomic_number", b"Algebra", b"Amino_acid",
    b"Asia", b"Africa", b"Australia", b"Antarctica", b"Atlantic_Ocean",
    b"Amazon", b"Arctic", b"Astronomy", b"Astrology", b"Architecture",
]


def _lcg(seed: int):
    """Numerical Recipes LCG; produces uint32 stream."""
    state = seed & 0xFFFFFFFF
    while True:
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        yield state


def generate(target_size: int, seed: int = 0xDECADECA) -> bytes:
    out: list[bytes] = []
    rng = _lcg(seed)
    written = 0

    out.append(b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/" '
               b'xml:lang="en">\n')
    written += len(out[-1])

    page_id = 1
    while written < target_size:
        title = TITLES[next(rng) % len(TITLES)]
        page = []
        page.append(b"  <page>\n    <title>")
        page.append(title)
        page.append(b"</title>\n    <id>")
        page.append(str(page_id).encode("ascii"))
        page.append(b"</id>\n    <revision>\n      <id>")
        page.append(str(1000 + page_id).encode("ascii"))
        page.append(b'</id>\n      <text xml:space="preserve">')
        # generate a deterministic text body
        n_tokens = 50 + (next(rng) % 200)
        body = []
        for _ in range(n_tokens):
            r = next(rng)
            if r % 17 == 0:
                body.append(b"[[")
                body.append(TITLES[next(rng) % len(TITLES)])
                body.append(b"]]")
            elif r % 23 == 0:
                body.append(b"{{cite|year=")
                body.append(str(1500 + (next(rng) % 525)).encode("ascii"))
                body.append(b"}}")
            elif r % 31 == 0:
                y = 1500 + (next(rng) % 525)
                m = 1 + (next(rng) % 12)
                d = 1 + (next(rng) % 28)
                body.append(f"{y:04d}-{m:02d}-{d:02d}".encode("ascii"))
            else:
                body.append(VOCAB[r % len(VOCAB)])
            body.append(b" ")
        page.append(b"".join(body).rstrip())
        page.append(b"</text>\n    </revision>\n  </page>\n")
        chunk = b"".join(page)
        if written + len(chunk) > target_size:
            # truncate cleanly
            chunk = chunk[: target_size - written]
            out.append(chunk)
            written += len(chunk)
            break
        out.append(chunk)
        written += len(chunk)
        page_id += 1

    out.append(b"</mediawiki>\n")
    result = b"".join(out)
    if len(result) > target_size:
        result = result[:target_size]
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=10_000_000,
                    help="target size in bytes (default 10 MB)")
    ap.add_argument("--seed", type=int, default=0xDECADECA)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()
    data = generate(args.size, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    import hashlib
    print(f"wrote {len(data)} bytes to {args.out}")
    print(f"md5: {hashlib.md5(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
