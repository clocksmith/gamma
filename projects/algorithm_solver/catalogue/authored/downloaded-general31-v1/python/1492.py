"""1492. The kth Factor of n (Medium).

Specification: https://leetcode.com/problems/the-kth-factor-of-n/description/
"""


def solve(n: int, k: int) -> int:
    count = 0
    for value in range(1, n + 1):
        if n % value == 0:
            count += 1
            if count == k:
                return value
    return -1


class Solution:
    def kthFactor(self, n: int, k: int) -> int:
        return solve(n, k)
