"""451. Sort Characters By Frequency. Descending frequencies with deterministic character-order ties."""

from collections import Counter

def solve(s: str) -> str:
    counts = Counter(s)
    return ''.join(char * count for char, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))


class Solution:
    def frequencySort(self, s: str) -> str:
        return solve(s)
