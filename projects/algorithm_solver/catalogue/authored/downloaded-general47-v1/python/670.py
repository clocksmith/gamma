"""670. Maximum Swap (Medium).

Specification: https://leetcode.com/problems/maximum-swap/description/
"""


def solve(num: int) -> int:
    digits = [int(ch) for ch in str(num)]
    last = [-1] * 10
    for i, d in enumerate(digits):
        last[d] = i
    for i, d in enumerate(digits):
        for digit in range(9, d, -1):
            if last[digit] > i:
                digits[i], digits[last[digit]] = digits[last[digit]], digits[i]
                return int("".join(str(v) for v in digits))
    return num


class Solution:
    def maximumSwap(self, num: int) -> int:
        return solve(num)
