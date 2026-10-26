"""1065. Index Pairs of a String (Easy).

Specification: https://leetcode.com/problems/index-pairs-of-a-string/description/
"""


def solve(text: str, words: list[str]) -> list[list[int]]:
    """O(n * totalWordLength + p log p) time, O(p) output space; report all overlapping matches."""
    result = []
    for start in range(len(text)):
        for word in words:
            if text.startswith(word, start):
                result.append([start, start + len(word) - 1])
    result.sort()
    return result


class Solution:
    def indexPairs(self, text: str, words: list[str]) -> list[list[int]]:
        return solve(text, words)
