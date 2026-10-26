"""1119. Remove Vowels from a String (Easy).

Specification: https://leetcode.com/problems/remove-vowels-from-a-string/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; remove lowercase English vowels while preserving order."""
    vowels = set('aeiou')
    return ''.join(character for character in s if character not in vowels)


class Solution:
    def removeVowels(self, s: str) -> str:
        return solve(s)
