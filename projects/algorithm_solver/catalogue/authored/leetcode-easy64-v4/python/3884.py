"""3884. First Matching Character From Both Ends (Easy).

Specification: https://leetcode.com/problems/first-matching-character-from-both-ends/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; include the center character when the length is odd."""
    left = 0
    right = len(s) - 1
    while left <= right:
        if s[left] == s[right]:
            return left
        left += 1
        right -= 1
    return -1


class Solution:
    def firstMatchingIndex(self, s: str) -> int:
        return solve(s)
