"""459. Repeated Substring Pattern (Easy).

Specification: https://leetcode.com/problems/repeated-substring-pattern/description/
"""


def solve(s: str) -> bool:
    """O(n) time and space; the longest proper border determines a candidate period."""
    prefix = [0] * len(s)
    for index in range(1, len(s)):
        matched = prefix[index - 1]
        while matched > 0 and s[index] != s[matched]:
            matched = prefix[matched - 1]
        if s[index] == s[matched]:
            matched += 1
        prefix[index] = matched
    border = prefix[-1]
    return border > 0 and len(s) % (len(s) - border) == 0


class Solution:
    def repeatedSubstringPattern(self, s: str) -> bool:
        return solve(s)
