"""Hack2Hire 677c923c5cbaff553b53b070 (Subset Sum Equals K) over an INFERRED spec; qualification unknown."""

def solve(nums, k):
    counts = {}
    for x in nums:
        counts[x] = counts.get(x, 0) + 1
    values = sorted(counts)
    d = len(values)
    mask = (1 << (k + 1)) - 1
    suffix = [0] * (d + 1)
    suffix[d] = 1
    for i in range(d - 1, -1, -1):
        v, acc, shifted = values[i], suffix[i + 1], suffix[i + 1]
        for _ in range(counts[values[i]]):
            shifted = (shifted << v) & mask
            if not shifted:
                break
            acc |= shifted
        suffix[i] = acc
    out = []
    if not suffix[0] >> k & 1:
        return out
    combo = []

    def walk(i, rest):
        if rest == 0:
            out.append(combo[:])
            return
        v = values[i]
        top = min(counts[v], rest // v)
        combo.extend([v] * top)
        for j in range(top, -1, -1):
            if suffix[i + 1] >> (rest - j * v) & 1:
                walk(i + 1, rest - j * v)
            if j:
                combo.pop()

    walk(0, k)
    return out


class Solution:
    def uniqueCombinations(self, nums, k):
        return solve(nums, k)
