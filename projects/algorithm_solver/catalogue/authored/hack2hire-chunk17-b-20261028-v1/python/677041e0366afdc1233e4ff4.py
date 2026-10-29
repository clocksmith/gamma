"""Hack2Hire 677041e0366afdc1233e4ff4 (Find Redundant Substring) over an INFERRED spec; qualification unknown."""


def solve(word, a, b):
    vowel_step = 1 - a
    consonant_step = 1 - b
    seen = {0: 1}
    key = 0
    total = 0
    for ch in word:
        key += vowel_step if ch in 'aeiou' else consonant_step
        count = seen.get(key, 0)
        total += count
        seen[key] = count + 1
    return total


class Solution:
    def countRedundantSubstrings(self, word, a, b):
        return solve(word, a, b)
