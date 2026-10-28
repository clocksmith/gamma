"""275. H-Index II (Medium).

Specification: https://leetcode.com/problems/h-index-ii/description/
"""


def solve(citations: list[int]) -> int:
    n = len(citations)
    left, right = 0, n
    while left < right:
        mid = (left + right) // 2
        if citations[mid] >= n - mid:
            right = mid
        else:
            left = mid + 1
    return n - left


class Solution:
    def hIndex(self, citations: list[int]) -> int:
        return solve(citations)
