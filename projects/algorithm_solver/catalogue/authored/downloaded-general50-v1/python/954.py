"""954. Array of Doubled Pairs (Medium).

Specification: https://leetcode.com/problems/array-of-doubled-pairs/description/
"""


def solve(arr: list[int]) -> bool:
    counts = {}
    for v in arr:
        counts[v] = counts.get(v, 0) + 1
    keys = sorted(counts.keys(), key=abs)
    for x in keys:
        need = counts.get(x, 0)
        if need == 0:
            continue
        if counts.get(2 * x, 0) < need:
            return False
        counts[2 * x] -= need
    return True


class Solution:
    def canReorderDoubled(self, arr: list[int]) -> bool:
        return solve(arr)
