"""992. Subarrays with K Different Integers (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/subarrays-with-k-different-integers/description/
Canonical API: solve(nums, k); also exposes Solution.subarraysWithKDistinct.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(nums: list[int], k: int) -> int:
    def count_at_most(limit: int) -> int:
        if limit <= 0:
            return 0
        frequencies = {}
        left = 0
        total = 0
        for right, value in enumerate(nums):
            frequencies[value] = frequencies.get(value, 0) + 1
            while len(frequencies) > limit:
                removed = nums[left]
                left += 1
                frequencies[removed] -= 1
                if frequencies[removed] == 0:
                    del frequencies[removed]
            total += right - left + 1
        return total

    return count_at_most(k) - count_at_most(k - 1)

class Solution:
    def subarraysWithKDistinct(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
