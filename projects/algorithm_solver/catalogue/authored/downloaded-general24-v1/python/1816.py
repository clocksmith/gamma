"""1816. Truncate Sentence (Easy).

Specification: https://leetcode.com/problems/truncate-sentence/description/
"""


def solve(s: str, k: int) -> str:
    return " ".join(s.split(' ')[:k])


class Solution:
    def truncateSentence(self, s: str, k: int) -> str:
        return solve(s, k)
