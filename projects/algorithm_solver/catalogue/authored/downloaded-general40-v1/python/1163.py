"""1163. Last Substring in Lexicographical Order (Hard).

Specification: https://leetcode.com/problems/last-substring-in-lexicographical-order/description/
Straightforward suffix comparison: correct, O(n squared) worst case, not
the optimal two-pointer algorithm.
"""


def solve(s: str) -> str:
    best = 0
    for i in range(1, len(s)):
        if s[i:] > s[best:]:
            best = i
    return s[best:]


class Solution:
    def lastSubstring(self, s: str) -> str:
        return solve(s)
