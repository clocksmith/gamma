"""738. Monotone Increasing Digits (Medium).

Specification: https://leetcode.com/problems/monotone-increasing-digits/description/
"""


def solve(n: int) -> int:
    digits = list(str(n))
    marker = len(digits)
    for i in range(len(digits) - 1, 0, -1):
        if digits[i] < digits[i - 1]:
            digits[i - 1] = str(int(digits[i - 1]) - 1)
            marker = i
    for i in range(marker, len(digits)):
        digits[i] = '9'
    return int("".join(digits))


class Solution:
    def monotoneIncreasingDigits(self, n: int) -> int:
        return solve(n)
