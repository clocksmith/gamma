"""1775. Equal Sum Arrays With Minimum Number of Operations: spend the largest available per-element sum improvements first."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n + m) time and O(1) auxiliary space for values from 1 through 6; inputs are read-only."""
    if len(nums1) > 6 * len(nums2) or len(nums2) > 6 * len(nums1):
        return -1
    low, high = nums1, nums2
    low_sum, high_sum = sum(low), sum(high)
    if low_sum > high_sum:
        low, high = high, low
        low_sum, high_sum = high_sum, low_sum
    difference = high_sum - low_sum
    gains = [0] * 6
    for value in low:
        gains[6 - value] += 1
    for value in high:
        gains[value - 1] += 1
    answer = 0
    for gain in range(5, 0, -1):
        if difference <= 0:
            return answer
        count = min(gains[gain], (difference + gain - 1) // gain)
        difference -= count * gain
        answer += count
    return answer if difference <= 0 else -1


class Solution:
    def minOperations(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
