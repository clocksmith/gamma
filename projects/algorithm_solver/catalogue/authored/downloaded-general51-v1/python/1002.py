"""1002. Find Common Characters (Easy).

Specification: https://leetcode.com/problems/find-common-characters/description/
"""


def solve(words: list[str]) -> list[str]:
    min_counts = [float('inf')] * 26
    for word in words:
        counts = [0] * 26
        for ch in word:
            counts[ord(ch) - 97] += 1
        for i in range(26):
            min_counts[i] = min(min_counts[i], counts[i])
    result = []
    for i in range(26):
        for _k in range(min_counts[i]):
            result.append(chr(97 + i))
    return result


class Solution:
    def commonChars(self, words: list[str]) -> list[str]:
        return solve(words)
