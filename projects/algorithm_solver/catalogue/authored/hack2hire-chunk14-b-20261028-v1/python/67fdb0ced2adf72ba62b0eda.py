"""Hack2Hire 67fdb0ced2adf72ba62b0eda (Vowels Substring) over an INFERRED spec; qualification unknown."""


def solve(s):
    slot = {'a': 0, 'e': 1, 'i': 2, 'o': 3, 'u': 4}
    last = [-1] * 5
    start = 0
    total = 0
    for i, ch in enumerate(s):
        k = slot.get(ch)
        if k is None:
            start = i + 1
            last = [-1] * 5
            continue
        last[k] = i
        earliest = min(last)
        if earliest >= start:
            total += earliest - start + 1
    return total


class Solution:
    def countVowelSubstrings(self, s):
        return solve(s)
