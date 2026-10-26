"""2490. Circular Sentence (Easy).

Specification: https://leetcode.com/problems/circular-sentence/description/
"""


def solve(sentence: str) -> bool:
    """O(n) time, O(1) space; valid words are separated by single spaces."""
    if sentence[0] != sentence[-1]:
        return False
    for index in range(1, len(sentence) - 1):
        if sentence[index] == ' ' and sentence[index - 1] != sentence[index + 1]:
            return False
    return True


class Solution:
    def isCircularSentence(self, sentence: str) -> bool:
        return solve(sentence)
