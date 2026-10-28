"""1754. Largest Merge Of Two Strings (Medium).

Specification: https://leetcode.com/problems/largest-merge-of-two-strings/description/
"""


def solve(word1: str, word2: str) -> str:
    i, j = 0, 0
    result = ''
    while i < len(word1) and j < len(word2):
        if word1[i:] > word2[j:]:
            result += word1[i]
            i += 1
        else:
            result += word2[j]
            j += 1
    return result + word1[i:] + word2[j:]


class Solution:
    def largestMerge(self, word1: str, word2: str) -> str:
        return solve(word1, word2)
