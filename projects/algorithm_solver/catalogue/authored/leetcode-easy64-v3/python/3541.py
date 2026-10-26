"""3541. Find Most Frequent Vowel and Consonant (Easy).

Specification: https://leetcode.com/problems/find-most-frequent-vowel-and-consonant/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) alphabet space; a missing vowel or consonant category contributes zero."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    vowels = {0, 4, 8, 14, 20}
    vowel_maximum = 0
    consonant_maximum = 0
    for index, count in enumerate(counts):
        if index in vowels:
            vowel_maximum = max(vowel_maximum, count)
        else:
            consonant_maximum = max(consonant_maximum, count)
    return vowel_maximum + consonant_maximum


class Solution:
    def maxFreqSum(self, s: str) -> int:
        return solve(s)
