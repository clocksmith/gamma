"""3931. Check Adjacent Digit Differences (Easy).

Specification: https://leetcode.com/problems/check-adjacent-digit-differences/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; compare adjacent ASCII decimal digits."""
    for index in range(1, len(s)):
        if abs(ord(s[index]) - ord(s[index - 1])) > 2:
            return False
    return True


class Solution:
    def isAdjacentDiffAtMostTwo(self, s: str) -> bool:
        return solve(s)
