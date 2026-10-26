"""2595. Number of Even and Odd Bits (Easy).

Specification: https://leetcode.com/problems/number-of-even-and-odd-bits/description/
"""


def solve(n: int) -> list[int]:
    """O(log(n + 1)) time, O(1) space; bit positions start at zero."""
    result = [0, 0]
    remaining = n
    parity = 0
    while remaining > 0:
        result[parity] += remaining % 2
        remaining //= 2
        parity = 1 - parity
    return result


class Solution:
    def evenOddBit(self, n: int) -> list[int]:
        return solve(n)
