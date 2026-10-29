"""Hack2Hire 68d56825569e57bd10bbd432 (Text Box Formatter, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(sentences):
    width = max(len(s) for s in sentences)
    border = '+' + '-' * width + '+'
    out = []
    for sentence in sentences:
        out.append(border)
        out.append('|' + sentence.ljust(width) + '|')
        out.append(border)
    return out


class Solution:
    def formatBoxes(self, sentences):
        return solve(sentences)
