"""1528. Shuffle String (Easy).

Specification: https://leetcode.com/problems/shuffle-string/description/
"""


def solve(s: str, indices: list[int]) -> str:
    """O(n) time and space; preserve indices."""
    result = [''] * len(s)
    for index, character in enumerate(s):
        result[indices[index]] = character
    return ''.join(result)


class Solution:
    def restoreString(self, s: str, indices: list[int]) -> str:
        return solve(s, indices)
