"""2114. Maximum Number of Words Found in Sentences (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-words-found-in-sentences/description/
"""


def solve(sentences: list[str]) -> int:
    """O(total characters) time, O(1) space; count single-space word separators; preserve sentences."""
    maximum = 0
    for sentence in sentences:
        words = 1
        for character in sentence:
            if character == ' ':
                words += 1
        maximum = max(maximum, words)
    return maximum


class Solution:
    def mostWordsFound(self, sentences: list[str]) -> int:
        return solve(sentences)
