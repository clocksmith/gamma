"""3908. Valid Digit Number (Easy).

Specification: https://leetcode.com/problems/valid-digit-number/description/
"""


def solve(n: int, x: int) -> bool:
    """O(d) time and space; use the ordinary decimal representation, including zero."""
    digits = str(n)
    target = str(x)
    return digits[0] != target and target in digits


class Solution:
    def validDigit(self, n: int, x: int) -> bool:
        return solve(n, x)
