"""Hack2Hire 69beec3021f6ab4226963c1d (Counting Words in a Text) over an INFERRED spec; qualification unknown."""


def solve(text, k):
    freq = {}
    for word in text.lower().split(' '):
        if word:
            freq[word] = freq.get(word, 0) + 1
    if not freq:
        return []
    levels = sorted(set(freq.values()), reverse=True)
    cutoff = levels[min(k, len(levels)) - 1]
    keep = sorted((-f, w) for w, f in freq.items() if f >= cutoff)
    return [[w, -f] for f, w in keep]


class Solution:
    def topFrequencyWords(self, text, k):
        return solve(text, k)
