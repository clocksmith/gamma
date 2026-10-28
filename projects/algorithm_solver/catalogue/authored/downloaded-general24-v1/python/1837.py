"""1837. Sum of Digits in Base K (Easy).

Specification: https://leetcode.com/problems/sum-of-digits-in-base-k/description/
"""


def solve(n: int, k: int) -> int:
    total = 0
    value = n
    while value > 0:
        total += value % k
        value //= k
    return total


class Solution:
    def sumBase(self, n: int, k: int) -> int:
        return solve(n, k)
