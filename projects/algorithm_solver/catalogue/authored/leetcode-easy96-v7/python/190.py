"""190. Reverse Bits (Easy).

Specification: https://leetcode.com/problems/reverse-bits/description/
"""


def solve(n: int) -> int:
    """O(32) time, O(1) space; reverse exactly 32 bits and return an unsigned integer."""
    remaining = n & 0xffffffff
    result = 0
    for _ in range(32):
        result = result * 2 + (remaining & 1)
        remaining >>= 1
    return result


class Solution:
    def reverseBits(self, n: int) -> int:
        return solve(n)
