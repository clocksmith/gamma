"""2918. Minimum Equal Sum of Two Arrays After Replacing Zeros: compare minimum positive replacements and whether each side can increase."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n + m) time and O(1) auxiliary space; inputs are read-only."""
    first = sum(nums1)
    second = sum(nums2)
    first_zeros = nums1.count(0)
    second_zeros = nums2.count(0)
    first += first_zeros
    second += second_zeros
    if first_zeros == 0 and first < second:
        return -1
    if second_zeros == 0 and second < first:
        return -1
    return max(first, second)


class Solution:
    def minSum(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
