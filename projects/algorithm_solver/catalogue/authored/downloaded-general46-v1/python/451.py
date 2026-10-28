"""451. Sort Characters By Frequency (Medium).

Specification: https://leetcode.com/problems/sort-characters-by-frequency/description/
"""


def solve(s: str) -> str:
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    entries = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    result = ''
    for ch, count in entries:
        result += ch * count
    return result


class Solution:
    def frequencySort(self, s: str) -> str:
        return solve(s)
