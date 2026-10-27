"""410. Split Array Largest Sum. Binary search the maximum segment sum for nonnegative inputs."""

def solve(nums: list[int], k: int) -> int:
    low, high = max(nums), sum(nums)
    while low < high:
        limit = (low + high) // 2
        parts, subtotal = 1, 0
        for value in nums:
            if subtotal + value > limit:
                parts += 1
                subtotal = 0
            subtotal += value
        if parts <= k:
            high = limit
        else:
            low = limit + 1
    return low


class Solution:
    def splitArray(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
