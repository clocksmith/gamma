"""3839. Number of Prefix Connected Groups."""
from __future__ import annotations
from collections import Counter


def solve(words: list[str], k: int) -> int:
    """O(n k) expected time and O(n k) space; each repeated prefix contributes one group."""
    counts = Counter(word[:k] for word in words if len(word) >= k)
    return sum(count >= 2 for count in counts.values())


class Solution:
    def prefixConnected(self, words: list[str], k: int) -> int:
        return solve(words, k)
