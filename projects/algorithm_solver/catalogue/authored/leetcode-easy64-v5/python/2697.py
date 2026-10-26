"""2697. Lexicographically Smallest Palindrome (Easy).

Specification: https://leetcode.com/problems/lexicographically-smallest-palindrome/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; choose the smaller letter in each mirrored pair."""
    characters = list(s)
    for left in range(len(characters) // 2):
        right = len(characters) - left - 1
        smaller = min(characters[left], characters[right])
        characters[left] = smaller
        characters[right] = smaller
    return ''.join(characters)


class Solution:
    def makeSmallestPalindrome(self, s: str) -> str:
        return solve(s)
