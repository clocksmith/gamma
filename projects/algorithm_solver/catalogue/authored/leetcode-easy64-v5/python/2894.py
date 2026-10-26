"""2894. Divisible and Non-divisible Sums Difference (Easy).

Specification: https://leetcode.com/problems/divisible-and-non-divisible-sums-difference/description/
"""


def solve(n: int, m: int) -> int:
    """O(1) time and space; all arithmetic is exact in the declared integer domain."""
    multiples = n // m
    return n * (n + 1) // 2 - m * multiples * (multiples + 1)


class Solution:
    def differenceOfSums(self, n: int, m: int) -> int:
        return solve(n, m)
