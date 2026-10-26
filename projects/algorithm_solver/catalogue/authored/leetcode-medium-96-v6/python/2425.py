"""2425. Bitwise XOR of All Pairings: cancel values repeated an even number of times across all pairings."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n + m) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only."""
    answer = 0
    if len(nums2) % 2:
        for value in nums1:
            answer ^= value
    if len(nums1) % 2:
        for value in nums2:
            answer ^= value
    return answer


class Solution:
    def xorAllNums(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
