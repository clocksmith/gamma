"""693. Binary Number with Alternating Bits (Easy).

Specification: https://leetcode.com/problems/binary-number-with-alternating-bits/description/
"""


def solve(n: int) -> bool:
    combined = n ^ (n >> 1)
    return (combined & (combined + 1)) == 0


class Solution:
    def hasAlternatingBits(self, n: int) -> bool:
        return solve(n)
