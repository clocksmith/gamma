"""2239. Find Closest Number to Zero (Easy).

Specification: https://leetcode.com/problems/find-closest-number-to-zero/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; prefer the larger value on equal absolute distance; preserve nums."""
    best = nums[0]
    for value in nums:
        if abs(value) < abs(best) or (abs(value) == abs(best) and value > best):
            best = value
    return best


class Solution:
    def findClosestNumber(self, nums: list[int]) -> int:
        return solve(nums)
