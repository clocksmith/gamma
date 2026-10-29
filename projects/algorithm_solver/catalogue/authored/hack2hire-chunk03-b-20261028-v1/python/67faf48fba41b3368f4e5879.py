"""Hack2Hire 67faf48fba41b3368f4e5879 (N-gram Split, level 2) over an INFERRED spec; qualification unknown."""


def solve(text, ngrams):
    root = {}
    for entry in ngrams:
        node = root
        for word in entry.split(' '):
            node = node.setdefault(word, {})
        node[None] = True  # terminal marker; words are never None
    words = text.split(' ')
    tokens, i = [], 0
    while i < len(words):
        node, best, j = root, 1, i
        while j < len(words) and words[j] in node:
            node = node[words[j]]
            j += 1
            if None in node: best = j - i
        tokens.append(' '.join(words[i:i + best]))
        i += best
    return tokens


class Solution:
    def splitNgrams(self, text, ngrams):
        return solve(text, ngrams)
