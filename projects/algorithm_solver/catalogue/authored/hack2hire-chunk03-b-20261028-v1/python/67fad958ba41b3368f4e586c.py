"""Hack2Hire 67fad958ba41b3368f4e586c (N-gram Split, level 1) over an INFERRED spec; qualification unknown."""


def solve(text, bigrams):
    pairs = set(bigrams)
    words = text.split(' ')
    tokens, i = [], 0
    while i < len(words):
        if i + 1 < len(words) and words[i] + ' ' + words[i + 1] in pairs:
            tokens.append(words[i] + ' ' + words[i + 1])
            i += 2
        else:
            tokens.append(words[i])
            i += 1
    return tokens


class Solution:
    def splitBigrams(self, text, bigrams):
        return solve(text, bigrams)
