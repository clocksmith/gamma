"""2586. Count the Number of Vowel Strings in Range (Easy).

Specification: https://leetcode.com/problems/count-the-number-of-vowel-strings-in-range/description/
"""


def solve(words: list[str], left: int, right: int) -> int:
    """O(right - left + 1) time, O(1) space; both endpoints of each word must be vowels; preserve words."""
    vowels = 'aeiou'
    count = 0
    for index in range(left, right + 1):
        word = words[index]
        if word[0] in vowels and word[-1] in vowels:
            count += 1
    return count


class Solution:
    def vowelStrings(self, words: list[str], left: int, right: int) -> int:
        return solve(words, left, right)
