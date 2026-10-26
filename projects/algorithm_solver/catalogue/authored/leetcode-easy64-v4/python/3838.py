"""3838. Weighted Word Mapping (Easy).

Specification: https://leetcode.com/problems/weighted-word-mapping/description/
"""


def solve(words: list[str], weights: list[int]) -> str:
    """O(total characters) time, O(word count) output space; preserve words and weights."""
    result = []
    for word in words:
        weight = 0
        for character in word:
            weight += weights[ord(character) - ord('a')]
        result.append(chr(ord('z') - weight % 26))
    return ''.join(result)


class Solution:
    def mapWordWeights(self, words: list[str], weights: list[int]) -> str:
        return solve(words, weights)
