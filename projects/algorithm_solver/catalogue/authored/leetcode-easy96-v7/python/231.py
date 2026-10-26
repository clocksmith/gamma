"""231. Power of Two (Easy).

Specification: https://leetcode.com/problems/power-of-two/description/
"""


def solve(n: int) -> bool:
    """O(log n) time, O(1) space; use exact integer division on the signed 32-bit domain."""
    if n <= 0:
        return False
    value = n
    while value % 2 == 0:
        value //= 2
    return value == 1


class Solution:
    def isPowerOfTwo(self, n: int) -> bool:
        return solve(n)
