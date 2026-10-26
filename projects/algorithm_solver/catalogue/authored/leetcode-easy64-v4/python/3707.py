"""3707. Equal Score Substrings (Easy).

Specification: https://leetcode.com/problems/equal-score-substrings/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; require two nonempty substrings."""
    total = sum(ord(character) - ord('a') + 1 for character in s)
    leftScore = 0
    for index in range(len(s) - 1):
        leftScore += ord(s[index]) - ord('a') + 1
        if leftScore * 2 == total:
            return True
    return False


class Solution:
    def scoreBalance(self, s: str) -> bool:
        return solve(s)
