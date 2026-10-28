"""1903. Largest Odd Number in String (Easy).

Specification: https://leetcode.com/problems/largest-odd-number-in-string/description/
"""


def solve(num: str) -> str:
    for i in range(len(num) - 1, -1, -1):
        if int(num[i]) % 2 == 1:
            return num[:i + 1]
    return ""


class Solution:
    def largestOddNumber(self, num: str) -> str:
        return solve(num)
