"""2062. Count Vowel Substrings of a String (Easy).

Specification: https://leetcode.com/problems/count-vowel-substrings-of-a-string/description/
"""


def solve(word: str) -> int:
    """O(n) time, O(1) space; count valid starts after the latest consonant from vowel last positions."""
    vowels = 'aeiou'
    latest = [-1] * 5
    boundary = -1
    total = 0
    for index, character in enumerate(word):
        vowel = vowels.find(character)
        if vowel < 0:
            boundary = index
            continue
        latest[vowel] = index
        total += max(0, min(latest) - boundary)
    return total


class Solution:
    def countVowelSubstrings(self, word: str) -> int:
        return solve(word)
