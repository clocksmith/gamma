"""3005. Count Elements With Maximum Frequency (Easy).

Specification: https://leetcode.com/problems/count-elements-with-maximum-frequency/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; count occurrences, not only distinct values."""
    counts = {}
    maximum = 0
    for value in nums:
        count = counts.get(value, 0) + 1
        counts[value] = count
        maximum = max(maximum, count)
    total = 0
    for count in counts.values():
        if count == maximum:
            total += count
    return total


class Solution:
    def maxFrequencyElements(self, nums: list[int]) -> int:
        return solve(nums)
