"""1408. String Matching in an Array (Easy).

Specification: https://leetcode.com/problems/string-matching-in-an-array/description/
"""


def solve(words: list[str]) -> list[str]:
    """O(n^2 * L^2) conservative substring-search time, O(n) result space; preserve words."""
    result = []
    for index, word in enumerate(words):
        for other, candidate in enumerate(words):
            if index != other and word in candidate:
                result.append(word)
                break
    return result


class Solution:
    def stringMatching(self, words: list[str]) -> list[str]:
        return solve(words)
