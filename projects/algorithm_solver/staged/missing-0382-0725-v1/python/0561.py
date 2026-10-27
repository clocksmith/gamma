"""561. Array Partition. Pair adjacent sorted values; preserve the original array."""

def solve(nums: list[int]) -> int:
    return sum(sorted(nums)[::2])


class Solution:
    def arrayPairSum(self, nums: list[int]) -> int:
        return solve(nums)
