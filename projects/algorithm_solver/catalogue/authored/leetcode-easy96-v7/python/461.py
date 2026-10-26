"""461. Hamming Distance (Easy).

Specification: https://leetcode.com/problems/hamming-distance/description/
"""


def solve(x: int, y: int) -> int:
    """O(32) time, O(1) space; count differing bits of the declared nonnegative 31-bit inputs."""
    difference = x ^ y
    count = 0
    while difference:
        difference &= difference - 1
        count += 1
    return count


class Solution:
    def hammingDistance(self, x: int, y: int) -> int:
        return solve(x, y)
