"""1134. Armstrong Number (Easy).

Specification: https://leetcode.com/problems/armstrong-number/description/
"""


def solve(n: int) -> bool:
    """O(d) digit operations, O(d) space; sum the d-th powers of decimal digits."""
    digits = str(n)
    total = 0
    for character in digits:
        total += (ord(character) - 48) ** len(digits)
    return total == n


class Solution:
    def isArmstrong(self, n: int) -> bool:
        return solve(n)
