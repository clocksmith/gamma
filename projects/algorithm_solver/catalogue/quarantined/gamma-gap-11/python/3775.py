"""3775. Reverse Words With Same Vowel Count."""
from __future__ import annotations


def solve(s: str) -> str:
    """O(n) time and O(n) space; preserve the first word and single-space separators."""
    words = s.split(' ')
    vowels = set('aeiou')
    target = sum(char in vowels for char in words[0])
    for index in range(1, len(words)):
        if sum(char in vowels for char in words[index]) == target:
            words[index] = words[index][::-1]
    return ' '.join(words)


class Solution:
    def reverseWords(self, s: str) -> str:
        return solve(s)
