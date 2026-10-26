"""1832. Check if the Sentence Is Pangram (Easy).

Specification: https://leetcode.com/problems/check-if-the-sentence-is-pangram/description/
"""


def solve(sentence: str) -> bool:
    """O(n) time, O(1) alphabet space; the input uses lowercase ASCII letters."""
    return len(set(sentence)) == 26


class Solution:
    def checkIfPangram(self, sentence: str) -> bool:
        return solve(sentence)
