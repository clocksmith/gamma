"""1317. Convert Integer to the Sum of Two No-Zero Integers (Easy).

Specification: https://leetcode.com/problems/convert-integer-to-the-sum-of-two-no-zero-integers/description/
"""


def solve(n: int) -> list[int]:
    """O(n log n) time, O(1) auxiliary space; choose the first valid pair."""
    def has_zero(value: int) -> bool:
        while value > 0:
            if value % 10 == 0:
                return True
            value //= 10
        return False

    for first in range(1, n):
        second = n - first
        if not has_zero(first) and not has_zero(second):
            return [first, second]
    return []


class Solution:
    def getNoZeroIntegers(self, n: int) -> list[int]:
        return solve(n)
