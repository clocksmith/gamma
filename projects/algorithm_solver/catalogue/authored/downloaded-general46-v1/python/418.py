"""418. Sentence Screen Fitting (Medium).

Specification: https://leetcode.com/problems/sentence-screen-fitting/description/
"""


def solve(sentence: list[str], rows: int, cols: int) -> int:
    word_index = 0
    completed = 0
    for _row in range(rows):
        remaining = cols
        while remaining >= len(sentence[word_index]):
            remaining -= len(sentence[word_index]) + 1
            word_index += 1
            if word_index == len(sentence):
                word_index = 0
                completed += 1
    return completed


class Solution:
    def wordsTyping(self, sentence: list[str], rows: int, cols: int) -> int:
        return solve(sentence, rows, cols)
