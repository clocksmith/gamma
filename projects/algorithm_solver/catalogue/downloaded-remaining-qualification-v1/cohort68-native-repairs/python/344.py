"""344. Reverse String (Easy).

Specification: https://leetcode.com/problems/reverse-string/description/
"""


def solve(s: list[str]) -> list[str]:
    return s[::-1]


class Solution:
    def reverseString(self, s: list[str]) -> None:
        left, right = 0, len(s) - 1
        while left < right:
            s[left], s[right] = s[right], s[left]
            left += 1
            right -= 1
