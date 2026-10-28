"""1768. Merge Strings Alternately (Easy).

Specification: https://leetcode.com/problems/merge-strings-alternately/description/
"""


def solve(word1: str, word2: str) -> str:
    result = ''
    for i in range(max(len(word1), len(word2))):
        if i < len(word1):
            result += word1[i]
        if i < len(word2):
            result += word2[i]
    return result


class Solution:
    def mergeAlternately(self, word1: str, word2: str) -> str:
        return solve(word1, word2)
