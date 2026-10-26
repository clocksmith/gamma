"""504. Base 7 (Easy).

Specification: https://leetcode.com/problems/base-7/description/
"""


def solve(num: int) -> str:
    """O(log(abs(num) + 1)) time and output space; preserve the sign and handle zero explicitly."""
    if num == 0:
        return '0'
    remaining = abs(num)
    digits = []
    while remaining > 0:
        digits.append(str(remaining % 7))
        remaining //= 7
    return ('-' if num < 0 else '') + ''.join(reversed(digits))


class Solution:
    def convertToBase7(self, num: int) -> str:
        return solve(num)
