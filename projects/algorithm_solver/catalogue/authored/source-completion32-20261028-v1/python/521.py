# 521 — Longest Uncommon Subsequence I. Original implementation; authored candidate, not independently qualified.
def solve(a, b):
    return -1 if a == b else max(len(a), len(b))

findLUSlength = solve

class Solution:
    findLUSlength = staticmethod(solve)
