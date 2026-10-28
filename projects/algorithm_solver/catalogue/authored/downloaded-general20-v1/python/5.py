"""5. Longest Palindromic Substring (Medium).

Specification: https://leetcode.com/problems/longest-palindromic-substring/description/
"""


def _expand(s, left, right):
    while left >= 0 and right < len(s) and s[left] == s[right]:
        left -= 1
        right += 1
    return left + 1, right - left - 1


def solve(s: str) -> str:
    start = 0
    length = 0
    for center in range(len(s)):
        for candidate_start, candidate_length in (_expand(s, center, center), _expand(s, center, center + 1)):
            if candidate_length > length:
                start = candidate_start
                length = candidate_length
    return s[start:start + length]


class Solution:
    def longestPalindrome(self, s: str) -> str:
        return solve(s)
