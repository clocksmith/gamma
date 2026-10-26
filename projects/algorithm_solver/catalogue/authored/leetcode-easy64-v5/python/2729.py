"""2729. Check if The Number is Fascinating (Easy).

Specification: https://leetcode.com/problems/check-if-the-number-is-fascinating/description/
"""


def solve(n: int) -> bool:
    """O(1) time and space for the three-digit input domain."""
    digits = str(n) + str(2 * n) + str(3 * n)
    if len(digits) != 9:
        return False
    seen = set()
    for digit in digits:
        if digit == '0' or digit in seen:
            return False
        seen.add(digit)
    return True


class Solution:
    def isFascinating(self, n: int) -> bool:
        return solve(n)
