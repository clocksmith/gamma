"""3456. Find Special Substring of Length K (Easy).

Specification: https://leetcode.com/problems/find-special-substring-of-length-k/description/
"""


def solve(s: str, k: int) -> bool:
    """O(n) time, O(1) space; a maximal equal-character run must have length exactly k."""
    start = 0
    while start < len(s):
        end = start + 1
        while end < len(s) and s[end] == s[start]:
            end += 1
        if end - start == k:
            return True
        start = end
    return False


class Solution:
    def hasSpecialSubstring(self, s: str, k: int) -> bool:
        return solve(s, k)
