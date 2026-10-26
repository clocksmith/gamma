"""2871. Split Array Into Maximum Number of Subarrays: cut as soon as the current bitwise AND is zero and otherwise keep one piece."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    current = -1
    pieces = 0
    for value in nums:
        current &= value
        if current == 0:
            pieces += 1
            current = -1
    return max(1, pieces)


class Solution:
    def maxSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
