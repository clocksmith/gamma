"""2220. Minimum Bit Flips to Convert Number (Easy).

Specification: https://leetcode.com/problems/minimum-bit-flips-to-convert-number/description/
"""


def solve(start: int, goal: int) -> int:
    """O(32) time, O(1) space; XOR identifies the bits that must change in the stated domain."""
    difference = start ^ goal
    flips = 0
    while difference:
        difference &= difference - 1
        flips += 1
    return flips


class Solution:
    def minBitFlips(self, start: int, goal: int) -> int:
        return solve(start, goal)
