"""Exact shared-substring enumeration without a maximum length cutoff."""
from __future__ import annotations


def suffix_array(values):
    """Prefix doubling: O(n log^2 n) comparisons of integer rank pairs, O(n) memory."""
    n = len(values)
    if not n:
        return []
    unique = {value: i for i, value in enumerate(sorted(set(values)))}
    rank = [unique[value] for value in values]
    sa = list(range(n))
    step = 1
    while True:
        sa.sort(key=lambda i: (rank[i], rank[i + step] if i + step < n else -1))
        updated = [0] * n
        for k in range(1, n):
            a, b = sa[k - 1], sa[k]
            updated[b] = updated[a] + ((rank[a], rank[a + step] if a + step < n else -1) !=
                                       (rank[b], rank[b + step] if b + step < n else -1))
        rank = updated
        if rank[sa[-1]] == n - 1:
            return sa
        step *= 2


def lcp_array(values, sa):
    """Kasai LCP with the preceding suffix; lcp[0]=0. O(n) time/memory."""
    n = len(values)
    rank = [0] * n
    for k, i in enumerate(sa):
        rank[i] = k
    out = [0] * n
    h = 0
    for i in range(n):
        k = rank[i]
        if not k:
            h = 0
            continue
        j = sa[k - 1]
        while i + h < n and j + h < n and values[i + h] == values[j + h]:
            h += 1
        out[k] = h
        h = max(0, h - 1)
    return out


def build_pool(texts, forbidden):
    """All distinct >=2-character strings shared by >=2 keys, excluding exact bans.

    Unique separators stop every cross-owner match at document boundaries.
    The best LCP with a differently owned suffix is achieved by the nearest
    differently owned suffix on either side in suffix order. Running minima
    within each same-owner run find those two LCPs in linear time. Emit lengths
    beyond the preceding suffix LCP: this outputs each distinct shared string
    exactly once, including prefixes of longer strings and repeated-owner runs.

    N is total input characters plus separators, S the bytes in all shared
    strings before exact bans, B the ban-set bytes. Time is O(N log^2 N+S+B);
    storage O(N+S+B). Explicit output can itself be quadratic in entries
    and cubic in bytes for adversarial input.
    """
    ordered = sorted(texts.items())
    count = len(ordered)
    values, owners, positions = [], [], []
    documents = [text for _, text in ordered]
    for owner, text in enumerate(documents):
        for offset, character in enumerate(text):
            values.append(ord(character) + count)
            owners.append(owner)
            positions.append(offset)
        values.append(owner)  # unique and smaller than any encoded character
        owners.append(-1)
        positions.append(-1)
    sa = suffix_array(values)
    lcp = lcp_array(values, sa)
    selected, adjacent = [], []
    minimum = None
    for k, start in enumerate(sa):
        minimum = lcp[k] if minimum is None else min(minimum, lcp[k])
        if owners[start] >= 0:
            selected.append(start)
            adjacent.append(0 if len(selected) == 1 else minimum)
            minimum = None
    n = len(selected)
    left = [0] * n
    right = [0] * n
    for i in range(1, n):
        left[i] = adjacent[i] if owners[selected[i]] != owners[selected[i - 1]] else min(left[i - 1], adjacent[i])
    for i in range(n - 2, -1, -1):
        right[i] = adjacent[i + 1] if owners[selected[i]] != owners[selected[i + 1]] else min(right[i + 1], adjacent[i + 1])
    banned = set(forbidden)
    output = []
    for i, start in enumerate(selected):
        text = documents[owners[start]]
        offset = positions[start]
        shared = min(max(left[i], right[i]), len(text) - offset)
        for length in range(max(2, adjacent[i] + 1), shared + 1):
            word = text[offset:offset + length]
            if word not in banned:
                output.append(word)
    return output
