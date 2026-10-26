"""1207. Unique Number of Occurrences (Easy).

Specification: https://leetcode.com/problems/unique-number-of-occurrences/description/
"""


def solve(arr: list[int]) -> bool:
    """O(n) expected time, O(n) space; preserve arr."""
    counts = {}
    for value in arr:
        counts[value] = counts.get(value, 0) + 1
    frequencies = set()
    for count in counts.values():
        if count in frequencies:
            return False
        frequencies.add(count)
    return True


class Solution:
    def uniqueOccurrences(self, arr: list[int]) -> bool:
        return solve(arr)
