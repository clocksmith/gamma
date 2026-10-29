"""Hack2Hire 68bad7afb5314dcd938cb9fe (Top 10 Words, variant 1 of 2) over an INFERRED spec; qualification unknown."""

import re

_WORD = re.compile('[A-Za-z]+')


def _better(word, count, other_word, other_count):
    return count > other_count or (count == other_count and word < other_word)


def solve(s):
    counts = {}
    for match in _WORD.findall(s):
        word = match.lower()
        counts[word] = counts.get(word, 0) + 1
    best = []
    for word, count in counts.items():
        if len(best) == 10 and not _better(word, count, best[-1][0], best[-1][1]):
            continue
        i = len(best)
        while i > 0 and _better(word, count, best[i - 1][0], best[i - 1][1]):
            i -= 1
        best.insert(i, [word, count])
        if len(best) > 10:
            best.pop()
    return best


class Solution:
    def topTenWords(self, s):
        return solve(s)
