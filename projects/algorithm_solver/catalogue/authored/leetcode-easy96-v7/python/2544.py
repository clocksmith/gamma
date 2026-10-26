"""2544. Alternating Digit Sum (Easy).

Specification: https://leetcode.com/problems/alternating-digit-sum/description/
"""


def solve(n: int) -> int:
    """O(d) time and digit-string space; alternate signs starting positive at the most significant digit."""
    result = 0
    sign = 1
    for character in str(n):
        result += sign * (ord(character) - 48)
        sign = -sign
    return result


class Solution:
    def alternateDigitSum(self, n: int) -> int:
        return solve(n)
