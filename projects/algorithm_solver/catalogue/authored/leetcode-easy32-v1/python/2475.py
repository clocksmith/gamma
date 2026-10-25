"""2475. Number of Unequal Triplets in Array (Easy).

Specification: https://leetcode.com/problems/number-of-unequal-triplets-in-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(u) space; count triples of distinct value groups."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    before = 0
    after = len(nums)
    result = 0
    for count in counts.values():
        after -= count
        result += before * count * after
        before += count
    return result


class Solution:
    def unequalTriplets(self, nums: list[int]) -> int:
        return solve(nums)
