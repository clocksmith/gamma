"""520. Detect Capital (Easy).

Specification: https://leetcode.com/problems/detect-capital/description/
"""


def solve(word: str) -> bool:
    """O(n) time, O(1) space; accept all lowercase, all uppercase, or just the first uppercase."""
    uppercase = sum('A' <= character <= 'Z' for character in word)
    return (uppercase == 0 or uppercase == len(word)
            or (uppercase == 1 and 'A' <= word[0] <= 'Z'))


class Solution:
    def detectCapitalUse(self, word: str) -> bool:
        return solve(word)
