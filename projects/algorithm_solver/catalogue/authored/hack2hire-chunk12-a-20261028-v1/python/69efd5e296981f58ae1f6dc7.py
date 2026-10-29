"""Hack2Hire 69efd5e296981f58ae1f6dc7 (Max Levels from Each Index) over an INFERRED spec; qualification unknown."""


def solve(layers, energy, K):
    n = len(layers)
    prefix = [0] * (n + 1)
    for i, v in enumerate(layers):
        prefix[i + 1] = prefix[i] + v
    out, j = [], 0
    for i in range(n):
        if j < i:
            j = i
        limit = K + prefix[i]
        while j < n and prefix[j + 1] + energy[j] <= limit:
            j += 1
        out.append(j - i)
    return out


class Solution:
    def maxLevels(self, layers, energy, K):
        return solve(layers, energy, K)
