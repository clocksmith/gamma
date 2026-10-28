"""418. Sentence Screen Fitting (Medium).

Specification: https://leetcode.com/problems/sentence-screen-fitting/description/
"""


def solve(sentence: list[str], rows: int, cols: int) -> int:
    text = ' '.join(sentence) + ' '
    cursor = 0
    for _ in range(rows):
        cursor += cols
        if text[cursor % len(text)] == ' ':
            cursor += 1
        else:
            while cursor > 0 and text[(cursor - 1) % len(text)] != ' ':
                cursor -= 1
    return cursor // len(text)


class Solution:
    def wordsTyping(self, sentence: list[str], rows: int, cols: int) -> int:
        return solve(sentence, rows, cols)
