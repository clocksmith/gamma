"""3790. Smallest All-Ones Multiple."""
from __future__ import annotations


def solve(k: int) -> int:
    """O(k) time and O(1) space; iterate remainders without constructing the large decimal integer."""
    if k % 2 == 0 or k % 5 == 0:
        return -1
    remainder = 0
    for length in range(1, k + 1):
        remainder = (remainder * 10 + 1) % k
        if remainder == 0:
            return length
    return -1


class Solution:
    def minAllOneMultiple(self, k: int) -> int:
        return solve(k)
