"""408. Valid Word Abbreviation."""

def solve(word: str, abbr: str) -> bool:
    i = j = 0
    while j < len(abbr):
        if '0' <= abbr[j] <= '9':
            if abbr[j] == '0':
                return False
            count = 0
            while j < len(abbr) and '0' <= abbr[j] <= '9':
                count = count * 10 + ord(abbr[j]) - 48
                j += 1
            i += count
            if i > len(word):
                return False
        else:
            if i >= len(word) or word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word)


class Solution:
    def validWordAbbreviation(self, word: str, abbr: str) -> bool:
        return solve(word, abbr)
