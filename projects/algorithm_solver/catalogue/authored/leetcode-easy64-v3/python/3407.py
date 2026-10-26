"""3407. Substring Matching Pattern (Easy).

Specification: https://leetcode.com/problems/substring-matching-pattern/description/
"""


def solve(s: str, p: str) -> bool:
    """O(|s| * |p|) worst-case time, O(|p|) space; the pattern contains one wildcard."""
    prefix, suffix = p.split('*')
    start = s.find(prefix)
    if start == -1:
        return False
    return s.find(suffix, start + len(prefix)) != -1


class Solution:
    def hasMatch(self, s: str, p: str) -> bool:
        return solve(s, p)
