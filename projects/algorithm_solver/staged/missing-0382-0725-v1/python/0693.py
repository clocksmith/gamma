"""693. Binary Number with Alternating Bits."""

def solve(n: int) -> bool:
    value = n ^ (n >> 1)
    return value & (value + 1) == 0


class Solution:
    def hasAlternatingBits(self, n: int) -> bool:
        return solve(n)
