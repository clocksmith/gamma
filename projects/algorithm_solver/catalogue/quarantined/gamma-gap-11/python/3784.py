"""3784. Minimum Deletion Cost to Make All Characters Equal."""
from __future__ import annotations


def solve(s: str, cost: list[int]) -> int:
    """O(n) time and O(26) space; retain every occurrence of the letter with maximum total deletion cost."""
    totals = [0] * 26
    for char, value in zip(s, cost):
        totals[ord(char) - 97] += value
    return sum(cost) - max(totals)


class Solution:
    def minCost(self, s: str, cost: list[int]) -> int:
        return solve(s, cost)
