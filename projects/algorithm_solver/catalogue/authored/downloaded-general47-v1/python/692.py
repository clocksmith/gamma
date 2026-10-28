"""692. Top K Frequent Words (Medium).

Specification: https://leetcode.com/problems/top-k-frequent-words/description/
"""


def solve(words: list[str], k: int) -> list[str]:
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    entries = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _count in entries[:k]]


class Solution:
    def topKFrequent(self, words: list[str], k: int) -> list[str]:
        return solve(words, k)
