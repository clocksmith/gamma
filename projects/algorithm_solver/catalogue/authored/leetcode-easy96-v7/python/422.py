"""422. Valid Word Square (Easy).

Specification: https://leetcode.com/problems/valid-word-square/description/
"""


def solve(words: list[str]) -> bool:
    """O(total characters) time, O(1) auxiliary space; check ragged transpose bounds; preserve words."""
    for row, word in enumerate(words):
        for column, character in enumerate(word):
            if column >= len(words) or row >= len(words[column]):
                return False
            if character != words[column][row]:
                return False
    return True


class Solution:
    def validWordSquare(self, words: list[str]) -> bool:
        return solve(words)
