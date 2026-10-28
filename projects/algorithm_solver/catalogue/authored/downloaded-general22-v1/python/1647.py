"""1647. Minimum Deletions to Make Character Frequencies Unique (Medium).

Specification: https://leetcode.com/problems/minimum-deletions-to-make-character-frequencies-unique/description/
"""


def solve(s: str) -> int:
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    frequencies = sorted(counts.values(), reverse=True)
    used = set()
    deletions = 0
    for freq in frequencies:
        while freq > 0 and freq in used:
            freq -= 1
            deletions += 1
        if freq > 0:
            used.add(freq)
    return deletions


class Solution:
    def minDeletions(self, s: str) -> int:
        return solve(s)
