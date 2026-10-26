"""2036. Maximum Alternating Subarray Sum: track nonempty contiguous sums ending with a plus or minus sign."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    plus = minus = float('-inf')
    best = nums[0]
    for value in nums:
        plus, minus = max(value, minus + value), plus - value
        best = max(best, plus, minus)
    return best


class Solution:
    def maximumAlternatingSubarraySum(self, nums: list[int]) -> int:
        return solve(nums)
