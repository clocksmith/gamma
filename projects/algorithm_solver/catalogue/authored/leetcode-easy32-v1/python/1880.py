"""1880. Check if Word Equals Summation of Two Words (Easy).

Specification: https://leetcode.com/problems/check-if-word-equals-summation-of-two-words/description/
"""


def solve(firstWord: str, secondWord: str, targetWord: str) -> bool:
    """O(total characters) time, O(1) space; a-j encode decimal digits."""
    def word_value(word: str) -> int:
        value = 0
        for character in word:
            value = value * 10 + ord(character) - ord('a')
        return value

    return word_value(firstWord) + word_value(secondWord) == word_value(targetWord)


class Solution:
    def isSumEqual(self, firstWord: str, secondWord: str, targetWord: str) -> bool:
        return solve(firstWord, secondWord, targetWord)
