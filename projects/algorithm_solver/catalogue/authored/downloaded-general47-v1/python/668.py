"""668. Kth Smallest Number in Multiplication Table (Hard).

Specification: https://leetcode.com/problems/kth-smallest-number-in-multiplication-table/description/
"""


def solve(m: int, n: int, k: int) -> int:
    left, right = 1, m * n
    while left < right:
        mid = (left + right) // 2
        count = sum(min(mid // i, n) for i in range(1, m + 1))
        if count < k:
            left = mid + 1
        else:
            right = mid
    return left


class Solution:
    def findKthNumber(self, m: int, n: int, k: int) -> int:
        return solve(m, n, k)
