"""3750. Minimum Number of Flips to Reverse Binary String (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-flips-to-reverse-binary-string/description/
"""


def solve(n: int) -> int:
    """O(log n) time and space; count mismatches with the original reversed representation."""
    digits = format(n, 'b')
    flips = 0
    for index in range(len(digits)):
        if digits[index] != digits[len(digits) - 1 - index]:
            flips += 1
    return flips


class Solution:
    def minimumFlips(self, n: int) -> int:
        return solve(n)
