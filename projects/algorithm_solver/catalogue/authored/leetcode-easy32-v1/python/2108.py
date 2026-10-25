"""2108. Find First Palindromic String in the Array (Easy).

Specification: https://leetcode.com/problems/find-first-palindromic-string-in-the-array/description/
"""


def solve(words: list[str]) -> str:
    """O(total characters) time, O(1) space; preserve the input word order."""
    for word in words:
        left = 0
        right = len(word) - 1
        while left < right and word[left] == word[right]:
            left += 1
            right -= 1
        if left >= right:
            return word
    return ''


class Solution:
    def firstPalindrome(self, words: list[str]) -> str:
        return solve(words)
