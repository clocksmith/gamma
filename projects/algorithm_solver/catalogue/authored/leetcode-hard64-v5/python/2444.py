"""2444. Count Subarrays With Fixed Bounds. Track the last invalid value and both required endpoints."""


def solve(nums: list[int], minK: int, maxK: int) -> int:
    """O(n) time and O(1) space. Inputs are preserved."""
    invalid = minimum = maximum = -1
    answer = 0
    for index, value in enumerate(nums):
        if value < minK or value > maxK:
            invalid = index
        if value == minK:
            minimum = index
        if value == maxK:
            maximum = index
        answer += max(0, min(minimum, maximum) - invalid)
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], minK: int, maxK: int) -> int:
        return solve(nums, minK, maxK)
