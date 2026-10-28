"""1332. Remove Palindromic Subsequences (Easy).

Specification: https://leetcode.com/problems/remove-palindromic-subsequences/description/
"""


def solve(s):
    if not s:
        return 0
    if s == s[::-1]:
        return 1
    return 2


class Solution:
    def removePalindromeSub(self, s):
        return solve(s)
