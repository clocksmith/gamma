"""418. Sentence Screen Fitting. Advance through a cyclic sentence without splitting words."""

def solve(sentence: list[str], rows: int, cols: int) -> int:
    text = ' '.join(sentence) + ' '
    length = len(text)
    position = 0
    for _ in range(rows):
        position += cols
        if text[position % length] == ' ':
            position += 1
        else:
            while position > 0 and text[(position - 1) % length] != ' ':
                position -= 1
    return position // length


class Solution:
    def wordsTyping(self, sentence: list[str], rows: int, cols: int) -> int:
        return solve(sentence, rows, cols)
