"""Hack2Hire 69e2411e95e80ae213e5d633 (Incremental String Tokenizer) over an INFERRED spec; qualification unknown."""


def solve(text, tokenAlphabet):
    alpha = tokenAlphabet
    m = len(alpha)
    ids = {token: i for i, token in enumerate(alpha)}
    k = 0
    while k < m and len(alpha[k]) == 1:
        k += 1
    n = len(text)
    val = [ids[c] for c in text]
    nxt = list(range(1, n + 1))
    prv = list(range(-1, n - 1))
    if n:
        nxt[-1] = -1
    alive = [True] * n
    pairs = {}

    def index(p):
        q = nxt[p]
        if q != -1:
            pairs.setdefault(val[p] * m + val[q], []).append(p)

    for p in range(n - 1):
        index(p)
    for j in range(k, m):
        token = alpha[j]
        keys, positions = set(), []
        for s in range(1, len(token)):
            a, b = ids.get(token[:s]), ids.get(token[s:])
            if a is None or b is None or a >= j or b >= j:
                continue
            key = a * m + b
            keys.add(key)
            positions.extend(pairs.pop(key, ()))
        if not positions:
            continue
        positions.sort()
        last = -1
        for p in positions:
            if p == last or not alive[p]:
                continue
            last = p
            q = nxt[p]
            if q == -1 or val[p] * m + val[q] not in keys:
                continue
            val[p] = j
            alive[q] = False
            r = nxt[q]
            nxt[p] = r
            if r != -1:
                prv[r] = p
            index(p)
            if prv[p] != -1:
                index(prv[p])
    out = []
    p = 0 if n else -1
    while p != -1:
        out.append(val[p])
        p = nxt[p]
    return out


class Solution:
    def tokenize(self, text, tokenAlphabet):
        return solve(text, tokenAlphabet)
