"""Hack2Hire 68d5a07e569e57bd10bbd44d (Text Box Formatter, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def _wrap(sentence, width):
    lines, current, size = [], [], 0
    for word in sentence.split(' '):
        if current and size + 1 + len(word) <= width:
            current.append(word)
            size += 1 + len(word)
        else:
            if current:
                lines.append(' '.join(current))
            current, size = [word], len(word)
    lines.append(' '.join(current))
    return lines


def solve(sentences, maxWidth):
    blocks = [_wrap(s, maxWidth) for s in sentences]
    width = max(len(line) for block in blocks for line in block)
    border = '+' + '-' * width + '+'
    out = []
    for block in blocks:
        out.append(border)
        for line in block:
            out.append('|' + line.ljust(width) + '|')
        out.append(border)
    return out


class Solution:
    def formatWrappedBoxes(self, sentences, maxWidth):
        return solve(sentences, maxWidth)
