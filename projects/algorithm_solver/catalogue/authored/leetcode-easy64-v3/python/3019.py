"""3019. Number of Changing Keys (Easy).

Specification: https://leetcode.com/problems/number-of-changing-keys/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) auxiliary space; compare neighboring ASCII letters case-insensitively."""
    result = 0
    for index in range(1, len(s)):
        if s[index].lower() != s[index - 1].lower():
            result += 1
    return result


class Solution:
    def countKeyChanges(self, s: str) -> int:
        return solve(s)
