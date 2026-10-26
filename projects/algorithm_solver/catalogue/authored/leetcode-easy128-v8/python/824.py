"""824. Goat Latin (Easy).

Specification: https://leetcode.com/problems/goat-latin/description/
"""


def solve(sentence: str) -> str:
    """O(n + w^2) time and space including the required growing suffixes."""
    words = sentence.split(' ')
    vowels = set('aeiouAEIOU')
    result = []
    for index, word in enumerate(words):
        stem = word if word[0] in vowels else word[1:] + word[0]
        result.append(stem + 'ma' + 'a' * (index + 1))
    return ' '.join(result)


class Solution:
    def toGoatLatin(self, sentence: str) -> str:
        return solve(sentence)
