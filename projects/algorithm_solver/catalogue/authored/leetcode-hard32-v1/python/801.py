"""801. Minimum Swaps To Make Sequences Increasing."""

def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) time, O(1) space; retain the best cost with the last pair kept or swapped."""
    keep, swap = 0, 1
    impossible = len(nums1) + 1
    for index in range(1, len(nums1)):
        next_keep = next_swap = impossible
        if nums1[index - 1] < nums1[index] and nums2[index - 1] < nums2[index]:
            next_keep = keep
            next_swap = swap + 1
        if nums1[index - 1] < nums2[index] and nums2[index - 1] < nums1[index]:
            next_keep = min(next_keep, swap)
            next_swap = min(next_swap, keep + 1)
        keep, swap = next_keep, next_swap
    return min(keep, swap)


class Solution:
    def minSwap(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
