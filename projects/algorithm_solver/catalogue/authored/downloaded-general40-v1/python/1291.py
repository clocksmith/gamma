"""1291. Sequential Digits (Medium).

Specification: https://leetcode.com/problems/sequential-digits/description/
"""


def solve(low: int, high: int) -> list[int]:
    result = []
    for length in range(2, 10):
        for start in range(1, 11 - length):
            value = 0
            for digit in range(length):
                value = value * 10 + start + digit
            if low <= value <= high:
                result.append(value)
    result.sort()
    return result


class Solution:
    def sequentialDigits(self, low: int, high: int) -> list[int]:
        return solve(low, high)
