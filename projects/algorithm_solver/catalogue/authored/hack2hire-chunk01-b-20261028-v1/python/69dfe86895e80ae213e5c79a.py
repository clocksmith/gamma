"""Hack2Hire 69dfe86895e80ae213e5c79a (Find Text Before Stop Words, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(text, stopWords):
    cut = len(text)
    for word in stopWords:
        position = text.find(word, 0, cut + len(word) - 1)
        if 0 <= position < cut:
            cut = position
    return text[:cut]


class Solution:
    def textBeforeStopWords(self, text, stopWords):
        return solve(text, stopWords)
