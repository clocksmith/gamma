"""408. Valid Word Abbreviation (Easy).

Specification: https://leetcode.com/problems/valid-word-abbreviation/description/
"""


def solve(word: str, abbr: str) -> bool:
    i = 0
    j = 0
    while i < len(word) and j < len(abbr):
        if abbr[j].isdigit():
            if abbr[j] == '0':
                return False
            number = 0
            while j < len(abbr) and abbr[j].isdigit():
                number = number * 10 + int(abbr[j])
                j += 1
            i += number
        else:
            if word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word) and j == len(abbr)


class Solution:
    def validWordAbbreviation(self, word: str, abbr: str) -> bool:
        return solve(word, abbr)
