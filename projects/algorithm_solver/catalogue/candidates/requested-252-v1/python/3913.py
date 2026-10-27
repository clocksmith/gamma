"""3913. Sort Vowels by Frequency
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/sort-vowels-by-frequency/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3913.Sort%20Vowels%20by%20Frequency/README_EN.md
Complexity: O(n) time and space (five vowel kinds).
Lowercase English; consonant positions fixed. Ties use first occurrence, not alphabetic order.
"""

from __future__ import annotations

def solve(s):
    counts = {}
    first = {}
    for index, character in enumerate(s):
        if character in 'aeiou':
            counts[character] = counts.get(character, 0) + 1
            first.setdefault(character, index)
    order = sorted(counts, key=lambda character: (-counts[character], first[character]))
    replacement = iter(''.join(character * counts[character] for character in order))
    return ''.join(next(replacement) if character in counts else character for character in s)


class Solution:
    def sortVowels(self, s):
        return solve(s)
