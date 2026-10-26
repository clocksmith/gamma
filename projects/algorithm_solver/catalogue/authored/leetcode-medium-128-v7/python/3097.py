"""3097. Shortest Subarray With OR at Least K II: maintain per-bit occurrence counts so a sliding-window OR can shrink safely."""


def solve(nums: list[int], k: int) -> int:
    """O(30 * n) time and O(30) auxiliary space on the bounded nonnegative integer domain; inputs are read-only."""
    counts = [0] * 30
    current = left = 0
    best = len(nums) + 1
    for right, value in enumerate(nums):
        current |= value
        for bit in range(30):
            if value & (1 << bit):
                counts[bit] += 1
        while left <= right and current >= k:
            best = min(best, right - left + 1)
            removed = nums[left]
            for bit in range(30):
                flag = 1 << bit
                if removed & flag:
                    counts[bit] -= 1
                    if counts[bit] == 0:
                        current ^= flag
            left += 1
    return best if best <= len(nums) else -1


class Solution:
    def minimumSubarrayLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
