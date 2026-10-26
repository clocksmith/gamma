"""2090. K Radius Subarray Averages: slide an exact integer sum over every complete centered window."""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time and O(n) result space; inputs are read-only."""
    width = 2 * k + 1
    result = [-1] * len(nums)
    if width > len(nums):
        return result
    total = 0
    for index, value in enumerate(nums):
        total += value
        if index >= width:
            total -= nums[index - width]
        if index >= width - 1:
            result[index - k] = total // width
    return result


class Solution:
    def getAverages(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
