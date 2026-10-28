"""2160. Minimum Sum of Four Digit Number After Splitting Digits (Easy).

Specification: https://leetcode.com/problems/minimum-sum-of-four-digit-number-after-splitting-digits/description/
"""


def solve(num: int) -> int:
    digits = sorted(int(ch) for ch in str(num))
    return (digits[0] * 10 + digits[2]) + (digits[1] * 10 + digits[3])


class Solution:
    def minimumSum(self, num: int) -> int:
        return solve(num)
