"""349. Intersection of Two Arrays."""
def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    return list(set(nums1) & set(nums2))

class Solution:
    def intersection(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
