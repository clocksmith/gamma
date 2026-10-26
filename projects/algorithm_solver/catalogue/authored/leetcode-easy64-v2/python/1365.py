"""1365. How Many Numbers Are Smaller Than the Current Number (Easy).

Specification: https://leetcode.com/problems/how-many-numbers-are-smaller-than-the-current-number/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n + 101) time, O(n + 101) space; preserve nums in the domain 0..100."""
    counts = [0] * 101
    for value in nums:
        counts[value] += 1
    smaller = 0
    for value in range(len(counts)):
        frequency = counts[value]
        counts[value] = smaller
        smaller += frequency
    return [counts[value] for value in nums]


class Solution:
    def smallerNumbersThanCurrent(self, nums: list[int]) -> list[int]:
        return solve(nums)
