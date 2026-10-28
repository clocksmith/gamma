"""647. Palindromic Substrings (Medium).

Specification: https://leetcode.com/problems/palindromic-substrings/description/
"""


def _expand(s, left, right):
    count = 0
    while left >= 0 and right < len(s) and s[left] == s[right]:
        count += 1
        left -= 1
        right += 1
    return count


def solve(s: str) -> int:
    total = 0
    for center in range(len(s)):
        total += _expand(s, center, center)
        total += _expand(s, center, center + 1)
    return total


class Solution:
    def countSubstrings(self, s: str) -> int:
        return solve(s)
