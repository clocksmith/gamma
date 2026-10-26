"""868. Binary Gap (Easy).

Specification: https://leetcode.com/problems/binary-gap/description/
"""


def solve(n: int) -> int:
    """O(log n) time, O(1) space; measure the distance between consecutive set-bit positions."""
    remaining = n
    position = 0
    previous = -1
    largest = 0
    while remaining > 0:
        if remaining % 2 == 1:
            if previous >= 0:
                largest = max(largest, position - previous)
            previous = position
        remaining //= 2
        position += 1
    return largest


class Solution:
    def binaryGap(self, n: int) -> int:
        return solve(n)
