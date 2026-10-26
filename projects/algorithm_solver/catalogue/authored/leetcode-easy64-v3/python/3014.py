"""3014. Minimum Number of Pushes to Type Word I (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-pushes-to-type-word-i/description/
"""


def solve(word: str) -> int:
    """O(1) time and space; distinct letters fill eight keys at each press depth."""
    full_levels, remainder = divmod(len(word), 8)
    return 4 * full_levels * (full_levels + 1) + remainder * (full_levels + 1)


class Solution:
    def minimumPushes(self, word: str) -> int:
        return solve(word)
