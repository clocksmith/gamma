"""1078. Occurrences After Bigram (Easy).

Specification: https://leetcode.com/problems/occurrences-after-bigram/description/
"""


def solve(text: str, first: str, second: str) -> list[str]:
    """O(total characters) time and space; preserve encounter order and overlapping bigrams."""
    words = text.split(' ')
    result = []
    for index in range(2, len(words)):
        if words[index - 2] == first and words[index - 1] == second:
            result.append(words[index])
    return result


class Solution:
    def findOcurrences(self, text: str, first: str, second: str) -> list[str]:
        return solve(text, first, second)
