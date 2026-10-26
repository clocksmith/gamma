"""2934. Minimum Operations to Maximize Last Elements in Arrays: compare keeping and swapping the last pair while independently fitting every earlier pair."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    def needed(first: int, second: int) -> int:
        swaps = 0
        for index in range(len(nums1) - 1):
            left, right = nums1[index], nums2[index]
            if left <= first and right <= second:
                continue
            if right > first or left > second:
                return len(nums1) + 1
            swaps += 1
        return swaps

    best = min(needed(nums1[-1], nums2[-1]), 1 + needed(nums2[-1], nums1[-1]))
    return best if best <= len(nums1) else -1


class Solution:
    def minOperations(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
