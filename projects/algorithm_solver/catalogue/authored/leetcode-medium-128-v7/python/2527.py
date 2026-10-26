"""2527. Find Xor-Beauty of Array: cancel the repeated triple contributions independently at each bit."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    result = 0
    for value in nums:
        result ^= value
    return result


class Solution:
    def xorBeauty(self, nums: list[int]) -> int:
        return solve(nums)
