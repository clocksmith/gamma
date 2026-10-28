"""2330. Valid Palindrome IV (Medium).

Specification: https://leetcode.com/problems/valid-palindrome-iv/description/
"""


def solve(s: str) -> bool:
    mismatches = 0
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            mismatches += 1
        l += 1
        r -= 1
    return mismatches <= 2


class Solution:
    def makePalindrome(self, s) -> object:
        return solve(s)
