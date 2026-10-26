"""1818. Minimum Absolute Sum Difference: find the best single replacement by binary searching a sorted copy."""
from bisect import bisect_left


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums1)
    total = improvement = 0
    for original, target in zip(nums1, nums2):
        difference = abs(original - target)
        total += difference
        index = bisect_left(ordered, target)
        nearest = difference
        if index < len(ordered):
            nearest = min(nearest, ordered[index] - target)
        if index > 0:
            nearest = min(nearest, target - ordered[index - 1])
        improvement = max(improvement, difference - nearest)
    return (total - improvement) % 1_000_000_007


class Solution:
    def minAbsoluteSumDiff(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
