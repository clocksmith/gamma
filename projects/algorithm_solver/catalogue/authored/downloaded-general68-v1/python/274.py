"""274. H-Index (Medium).

Specification: https://leetcode.com/problems/h-index/description/
"""


def solve(citations: list[int]) -> int:
    ordered = sorted(citations, reverse=True)
    h = 0
    for i, value in enumerate(ordered):
        if value >= i + 1:
            h = i + 1
        else:
            break
    return h


class Solution:
    def hIndex(self, citations: list[int]) -> int:
        return solve(citations)
