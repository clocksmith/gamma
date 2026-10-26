"""2040. Kth Smallest Product of Two Sorted Arrays."""

from bisect import bisect_left, bisect_right


def solve(nums1: list[int], nums2: list[int], k: int) -> int:
    """Binary search over products with sign-aware rank counts; O(n log m log R) time, O(1) auxiliary space. Inputs are preserved."""
    def enough(limit):
        count = 0
        for value in nums1:
            if value > 0:
                count += bisect_right(nums2, limit // value)
            elif value < 0:
                threshold = -((-limit) // value)
                count += len(nums2) - bisect_left(nums2, threshold)
            elif limit >= 0:
                count += len(nums2)
            if count >= k:
                return True
        return False

    corners = (nums1[0] * nums2[0], nums1[0] * nums2[-1],
               nums1[-1] * nums2[0], nums1[-1] * nums2[-1])
    left, right = min(corners), max(corners)
    while left < right:
        middle = (left + right) // 2
        if enough(middle):
            right = middle
        else:
            left = middle + 1
    return left


class Solution:
    def kthSmallestProduct(self, nums1: list[int], nums2: list[int], k: int) -> int:
        return solve(nums1, nums2, k)
