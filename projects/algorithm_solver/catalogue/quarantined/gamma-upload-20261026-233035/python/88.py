"""88. Merge Sorted Array."""
def solve(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    left, right, write = m - 1, n - 1, m + n - 1
    while right >= 0:
        if left >= 0 and nums1[left] > nums2[right]:
            nums1[write] = nums1[left]
            left -= 1
        else:
            nums1[write] = nums2[right]
            right -= 1
        write -= 1

class Solution:
    def merge(self, nums1: list[int], m: int, nums2: list[int], n: int) -> None:
        solve(nums1, m, nums2, n)
