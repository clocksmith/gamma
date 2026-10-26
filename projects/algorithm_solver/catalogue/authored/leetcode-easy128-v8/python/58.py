"""58. Length of Last Word (Easy).

Specification: https://leetcode.com/problems/length-of-last-word/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; skip trailing spaces and scan the final word."""
    index = len(s) - 1
    while index >= 0 and s[index] == ' ':
        index -= 1
    end = index
    while index >= 0 and s[index] != ' ':
        index -= 1
    return end - index


class Solution:
    def lengthOfLastWord(self, s: str) -> int:
        return solve(s)
