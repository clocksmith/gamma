"""3136. Valid Word (Easy).

Specification: https://leetcode.com/problems/valid-word/description/
"""


def solve(word: str) -> bool:
    """O(n) time, O(1) auxiliary space; accept ASCII letters/digits only, with a vowel and consonant."""
    if len(word) < 3:
        return False
    has_vowel = False
    has_consonant = False
    for character in word:
        if '0' <= character <= '9':
            continue
        lower = character.lower()
        if not 'a' <= lower <= 'z':
            return False
        if lower in 'aeiou':
            has_vowel = True
        else:
            has_consonant = True
    return has_vowel and has_consonant


class Solution:
    def isValid(self, word: str) -> bool:
        return solve(word)
