"""344. Reverse String (Easy).

Specification: https://leetcode.com/problems/reverse-string/description/
"""


def solve(s: list[str]) -> list[str]:
    return s[::-1]


class Solution:
    def reverseString(self, s: list[str]) -> list[str]:
        return solve(s)
