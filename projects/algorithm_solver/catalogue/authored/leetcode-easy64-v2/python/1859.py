"""1859. Sorting the Sentence (Easy).

Specification: https://leetcode.com/problems/sorting-the-sentence/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(n) space; at most nine words with unique trailing positions."""
    words = s.split(' ')
    ordered = [''] * len(words)
    for word in words:
        position = int(word[-1]) - 1
        ordered[position] = word[:-1]
    return ' '.join(ordered)


class Solution:
    def sortSentence(self, s: str) -> str:
        return solve(s)
