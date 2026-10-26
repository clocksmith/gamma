"""1437. Check If All 1's Are at Least Length K Places Away (Easy).

Specification: https://leetcode.com/problems/check-if-all-1s-are-at-least-length-k-places-away/description/
"""


def solve(nums: list[int], k: int) -> bool:
    """O(n) time, O(1) space; require at least k zeros between ones; preserve nums."""
    previous = -k - 1
    for index, value in enumerate(nums):
        if value == 1:
            if index - previous <= k:
                return False
            previous = index
    return True


class Solution:
    def kLengthApart(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
