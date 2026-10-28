"""500. Keyboard Row (Easy).

Specification: https://leetcode.com/problems/keyboard-row/description/
"""


ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]


def solve(words: list[str]) -> list[str]:
    answer = []
    for word in words:
        lower = word.lower()
        row = next(candidate for candidate in ROWS if lower[0] in candidate)
        if all(ch in row for ch in lower):
            answer.append(word)
    return answer


class Solution:
    def findWords(self, words: list[str]) -> list[str]:
        return solve(words)
