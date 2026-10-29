"""Hack2Hire 69e9376dfbaf3da6418286a5 (Find Balanced Prefix in Permutation) over an INFERRED spec; qualification unknown."""


def solve(p):
    n = len(p)
    pos = [0] * (n + 1)
    for i, v in enumerate(p):
        pos[v] = i
    lo = hi = pos[1]
    out = []
    for k in range(1, n + 1):
        lo = min(lo, pos[k])
        hi = max(hi, pos[k])
        out.append('1' if hi - lo + 1 == k else '0')
    return ''.join(out)


class Solution:
    def balancedNumbers(self, p):
        return solve(p)
