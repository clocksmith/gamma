"""3883. Count Non Decreasing Arrays With Given Digit Sums."""
from __future__ import annotations


def solve(digitSum: list[int]) -> int:
    """O(5001*n) time and O(5001) space; prefix-sum DP enforces nondecreasing values and exact decimal digit sums."""
    modulus = 1_000_000_007
    limit = 5000
    sums = [0] * (limit + 1)
    for value in range(1, limit + 1):
        sums[value] = sums[value // 10] + value % 10
    if any(wanted > 31 for wanted in digitSum):
        return 0
    previous = [0] * (limit + 1)
    previous[0] = 1
    for wanted in digitSum:
        current = [0] * (limit + 1)
        prefix = 0
        for value in range(limit + 1):
            prefix = (prefix + previous[value]) % modulus
            if sums[value] == wanted:
                current[value] = prefix
        previous = current
    return sum(previous) % modulus


class Solution:
    def countArrays(self, digitSum: list[int]) -> int:
        return solve(digitSum)
