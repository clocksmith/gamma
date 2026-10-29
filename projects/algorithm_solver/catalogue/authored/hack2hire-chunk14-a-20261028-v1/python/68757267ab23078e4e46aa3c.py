"""Hack2Hire 68757267ab23078e4e46aa3c (Split Text into Lines) over an INFERRED spec; qualification unknown."""


def solve(text, maxWidth):
    lines = 0
    current = 0
    for word in text.split(' '):
        if not word:
            continue
        if lines == 0 or current + 1 + len(word) > maxWidth:
            lines += 1
            current = len(word)
        else:
            current += 1 + len(word)
    return lines


class Solution:
    def minLines(self, text, maxWidth):
        return solve(text, maxWidth)
