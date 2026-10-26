"""1855. Maximum Distance Between a Pair of Values: advance monotone pointers while respecting the index ordering."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(len(nums1) + len(nums2)) time and O(1) auxiliary space; inputs are read-only."""
    left = right = best = 0
    while left < len(nums1) and right < len(nums2):
        if right < left:
            right = left
            continue
        if nums1[left] <= nums2[right]:
            best = max(best, right - left)
            right += 1
        else:
            left += 1
    return best


class Solution:
    def maxDistance(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
