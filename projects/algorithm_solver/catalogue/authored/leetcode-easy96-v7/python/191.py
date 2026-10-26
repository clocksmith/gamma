"""191. Number of 1 Bits (Easy).

Specification: https://leetcode.com/problems/number-of-1-bits/description/
"""


def solve(n: int) -> int:
    """O(32) time, O(1) space; count set bits in the unsigned 32-bit representation."""
    remaining = n & 0xffffffff
    count = 0
    while remaining:
        remaining &= remaining - 1
        count += 1
    return count


class Solution:
    def hammingWeight(self, n: int) -> int:
        return solve(n)
