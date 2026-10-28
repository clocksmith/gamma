"""2300. Successful Pairs of Spells and Potions (Medium).

Specification: https://leetcode.com/problems/successful-pairs-of-spells-and-potions/description/
"""


def solve(spells: list[int], potions: list[int], success: int) -> list[int]:
    import bisect
    import math
    sorted_p = sorted(potions)
    out = []
    for spell in spells:
        need = math.ceil(success / spell)
        idx = bisect.bisect_left(sorted_p, need)
        out.append(len(sorted_p) - idx)
    return out


class Solution:
    def successfulPairs(self, spells, potions, success) -> object:
        return solve(spells, potions, success)
