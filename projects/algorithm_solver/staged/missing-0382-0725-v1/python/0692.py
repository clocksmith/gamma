"""692. Top K Frequent Words. Sort distinct words by descending count and ascending lexical order."""

from collections import Counter

def solve(words: list[str], k: int) -> list[str]:
    counts = Counter(words)
    return sorted(counts, key=lambda word: (-counts[word], word))[:k]


class Solution:
    def topKFrequent(self, words: list[str], k: int) -> list[str]:
        return solve(words, k)
