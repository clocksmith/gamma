"""2270. Number of Ways to Split Array: compare each proper prefix with the remaining suffix using one running sum."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    total = sum(nums)
    prefix = answer = 0
    for index in range(len(nums) - 1):
        prefix += nums[index]
        if prefix >= total - prefix:
            answer += 1
    return answer


class Solution:
    def waysToSplitArray(self, nums: list[int]) -> int:
        return solve(nums)
