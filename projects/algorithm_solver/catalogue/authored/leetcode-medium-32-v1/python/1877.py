"""1877. Minimize Maximum Pair Sum in Array: pair opposite ends of a sorted copy."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    values = sorted(nums)
    best = 0
    for left in range(len(values) // 2):
        right = len(values) - left - 1
        best = max(best, values[left] + values[right])
    return best


class Solution:
    def minPairSum(self, nums: list[int]) -> int:
        return solve(nums)
