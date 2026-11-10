"""No-fallback flat-string dictionary fitting; never executes supplied source."""
from collections import Counter, defaultdict
import hashlib


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def alphabet(sources, capacity):
    """Bounded coverage-first character selection, retaining its frequency control."""
    counts = Counter(''.join(sources.values()))
    frequency = sorted(counts, key=lambda c: (-counts[c], c))[:capacity]
    sets = sorted({frozenset(s) for s in sources.values()}, key=lambda s: (len(s), ''.join(sorted(s))))
    if len(counts) <= capacity:
        return sorted(counts), frequency
    def coverage(chars):
        return sum(set(s) <= chars for s in sources.values())
    candidates = [set(frequency)]
    for seed in [set()] + [set(s) for s in sets[:8] if len(s) <= capacity]:
        chars = seed
        while True:
            choices = {frozenset(chars | s) for s in sets if not s <= chars and len(chars | s) <= capacity}
            if not choices:
                break
            chars = set(min(choices, key=lambda x: (-coverage(x), len(x), -sum(counts[c] for c in x), ''.join(sorted(x)))))
        for c in frequency + sorted(counts):
            if len(chars) < capacity:
                chars.add(c)
        candidates.append(chars)
    best = min(candidates, key=lambda x: (-coverage(x), -sum(counts[c] for c in x), ''.join(sorted(x))))
    return sorted(best), frequency


def pair_fit(sources, initial, capacity, banned, max_bytes=160):
    """Standard pair merges propose literal strings, stored flat, not recursive rules.

    Only completely representable fitting sources participate. Each proposed
    pair must occur in two distinct source hashes; overlapping pair occurrences
    are counted once. All accepted proposals and counts are retained.
    """
    dictionary = list(initial)
    available = set(initial)
    records = [(sha(s.encode()), list(s)) for s in sources.values() if set(s) <= available]
    trace = []
    by_length = defaultdict(list)
    for ban in banned:
        if ban and len(ban) <= max_bytes:
            by_length[len(ban)].append(ban)
    lengths = sorted(by_length)
    def prohibited(raw):
        stripped = raw.strip()
        for size in lengths:
            if size > len(stripped):
                break
            if any(b in stripped for b in by_length[size]):
                return True
        return False
    while len(dictionary) < capacity:
        counts = Counter()
        owners = defaultdict(set)
        for owner, seq in records:
            last = {}
            for i in range(len(seq) - 1):
                pair = (seq[i], seq[i + 1])
                if i < last.get(pair, -1):
                    continue
                last[pair] = i + 2
                counts[pair] += 1
                owners[pair].add(owner)
        choices = []
        for pair, count in counts.items():
            text = ''.join(pair)
            raw = text.encode()
            if text in available or len(owners[pair]) < 2 or len(raw) > max_bytes:
                continue
            if prohibited(raw):
                continue
            choices.append((pair, count, len(owners[pair])))
        if not choices:
            break
        pair, count, support = min(choices, key=lambda x: (-x[1], -x[2], len(''.join(x[0]).encode()), x[0]))
        text = ''.join(pair)
        dictionary.append(text)
        available.add(text)
        trace.append({'entry_sha256': sha(text.encode()), 'pair_count': count, 'distinct_source_hashes': support})
        new = []
        for owner, seq in records:
            merged = []
            i = 0
            while i < len(seq):
                if i + 1 < len(seq) and (seq[i], seq[i + 1]) == pair:
                    merged.append(text)
                    i += 2
                else:
                    merged.append(seq[i])
                    i += 1
            new.append((owner, merged))
        records = new
    return dictionary, trace
