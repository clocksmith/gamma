"""186. Reverse Words in a String II (Medium).

Specification: https://leetcode.com/problems/reverse-words-in-a-string-ii/description/
"""


def solve(s: list[str]) -> list[str]:
    chars = s[::-1]
    start = 0
    for i in range(len(chars) + 1):
        if i == len(chars) or chars[i] == ' ':
            left, right = start, i - 1
            while left < right:
                chars[left], chars[right] = chars[right], chars[left]
                left += 1
                right -= 1
            start = i + 1
    return chars


class Solution:
    def reverseWords(self, s: list[str]) -> list[str]:
        return solve(s)
