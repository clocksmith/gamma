"""2190. Most Frequent Number Following Key In an Array (Easy).

Specification: https://leetcode.com/problems/most-frequent-number-following-key-in-an-array/description/
"""


def solve(nums: list[int], key: int) -> int:
    """O(n) expected time, O(n) space; count immediate successors; the public domain guarantees a unique answer."""
    counts = {}
    best = -1
    largest_count = 0
    for index in range(len(nums) - 1):
        if nums[index] != key:
            continue
        value = nums[index + 1]
        count = counts.get(value, 0) + 1
        counts[value] = count
        if count > largest_count:
            largest_count = count
            best = value
    return best


class Solution:
    def mostFrequent(self, nums: list[int], key: int) -> int:
        return solve(nums, key)
