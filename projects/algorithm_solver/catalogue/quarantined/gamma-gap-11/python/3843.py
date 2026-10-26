"""3843. First Element with Unique Frequency."""
from __future__ import annotations
from collections import Counter


def solve(nums: list[int]) -> int:
    """O(n) expected time and space; distinguish an element frequency from the number of elements sharing it."""
    frequencies = Counter(nums)
    frequency_counts = Counter(frequencies.values())
    for value in nums:
        if frequency_counts[frequencies[value]] == 1:
            return value
    return -1


class Solution:
    def firstUniqueFreq(self, nums: list[int]) -> int:
        return solve(nums)
