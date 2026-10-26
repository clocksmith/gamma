"""3833. Count Dominant Indices (Easy).

Specification: https://leetcode.com/problems/count-dominant-indices/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; compare averages by exact cross multiplication; preserve nums."""
    suffixSum = nums[-1]
    suffixCount = 1
    result = 0
    for index in range(len(nums) - 2, -1, -1):
        if nums[index] * suffixCount > suffixSum:
            result += 1
        suffixSum += nums[index]
        suffixCount += 1
    return result


class Solution:
    def dominantIndices(self, nums: list[int]) -> int:
        return solve(nums)
