"""2404. Most Frequent Even Element (Easy).

Specification: https://leetcode.com/problems/most-frequent-even-element/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; break frequency ties by smaller value; preserve nums."""
    counts = {}
    best = -1
    largest_count = 0
    for value in nums:
        if value % 2:
            continue
        count = counts.get(value, 0) + 1
        counts[value] = count
        if count > largest_count or (count == largest_count and value < best):
            largest_count = count
            best = value
    return best


class Solution:
    def mostFrequentEven(self, nums: list[int]) -> int:
        return solve(nums)
