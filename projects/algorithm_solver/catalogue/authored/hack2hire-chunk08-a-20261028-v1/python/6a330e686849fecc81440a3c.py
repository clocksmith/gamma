"""Hack2Hire 6a330e686849fecc81440a3c (Prefix Frequency Partition) over an INFERRED spec; qualification unknown."""


def solve(s):
    n = len(s)
    codes = [ord(ch) - 65 for ch in s]
    pre = [0] * (26 * (n + 1))  # pre[26 * i + c] = count of letter c in s[0:i]
    for i, c in enumerate(codes):
        base = 26 * i
        pre[base + 26:base + 52] = pre[base:base + 26]
        pre[base + 26 + c] += 1
    letters = sorted(set(codes))
    out = []
    for size in range(1, n + 1):
        if n % size:
            continue
        want = [pre[26 * size + c] for c in letters]
        ok = True
        for k in range(2, n // size + 1):
            off = 26 * k * size
            for c, w in zip(letters, want):
                if pre[off + c] != k * w:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append(size)
    return out


class Solution:
    def validPrefixLengths(self, s):
        return solve(s)
