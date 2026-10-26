"""1662. Check If Two String Arrays are Equivalent (Easy).

Specification: https://leetcode.com/problems/check-if-two-string-arrays-are-equivalent/description/
"""


def solve(word1: list[str], word2: list[str]) -> bool:
    """O(total characters) time, O(1) space; compare nonempty input pieces without joining."""
    first_word = 0
    second_word = 0
    first_character = 0
    second_character = 0
    while first_word < len(word1) and second_word < len(word2):
        if word1[first_word][first_character] != word2[second_word][second_character]:
            return False
        first_character += 1
        second_character += 1
        if first_character == len(word1[first_word]):
            first_word += 1
            first_character = 0
        if second_character == len(word2[second_word]):
            second_word += 1
            second_character = 0
    return first_word == len(word1) and second_word == len(word2)


class Solution:
    def arrayStringsAreEqual(self, word1: list[str], word2: list[str]) -> bool:
        return solve(word1, word2)
