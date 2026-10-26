"""3162. Find the Number of Good Pairs I (Easy).

Specification: https://leetcode.com/problems/find-the-number-of-good-pairs-i/description/
"""


def solve(nums1: list[int], nums2: list[int], k: int) -> int:
    """O(n * m) time, O(1) auxiliary space; all divisors are positive; preserve arrays."""
    pairs = 0
    for first in nums1:
        for second in nums2:
            if first % (second * k) == 0:
                pairs += 1
    return pairs


class Solution:
    def numberOfPairs(self, nums1: list[int], nums2: list[int], k: int) -> int:
        return solve(nums1, nums2, k)
