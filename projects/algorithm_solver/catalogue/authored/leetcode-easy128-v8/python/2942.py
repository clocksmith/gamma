"""2942. Find Words Containing Character (Easy).

Specification: https://leetcode.com/problems/find-words-containing-character/description/
"""


def solve(words: list[str], x: str) -> list[int]:
    """O(total characters) time, O(1) auxiliary space excluding output; preserve word indices."""
    return [index for index, word in enumerate(words) if x in word]


class Solution:
    def findWordsContaining(self, words: list[str], x: str) -> list[int]:
        return solve(words, x)
