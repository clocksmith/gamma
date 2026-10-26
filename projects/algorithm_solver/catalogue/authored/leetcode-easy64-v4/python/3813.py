"""3813. Vowel-Consonant Score (Easy).

Specification: https://leetcode.com/problems/vowel-consonant-score/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; ignore spaces and digits, and return zero without consonants."""
    vowels = 0
    consonants = 0
    for character in s:
        if character in 'aeiou':
            vowels += 1
        elif 'a' <= character <= 'z':
            consonants += 1
    return 0 if consonants == 0 else vowels // consonants


class Solution:
    def vowelConsonantScore(self, s: str) -> int:
        return solve(s)
