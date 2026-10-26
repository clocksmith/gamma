"""1829. Maximum XOR for Each Query: complement the active prefix XOR within the permitted bit mask."""


def solve(nums: list[int], maximumBit: int) -> list[int]:
    """O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only."""
    combined = 0
    for value in nums:
        combined ^= value
    mask = (1 << maximumBit) - 1
    result = []
    for index in range(len(nums) - 1, -1, -1):
        result.append(mask ^ combined)
        combined ^= nums[index]
    return result


class Solution:
    def getMaximumXor(self, nums: list[int], maximumBit: int) -> list[int]:
        return solve(nums, maximumBit)
