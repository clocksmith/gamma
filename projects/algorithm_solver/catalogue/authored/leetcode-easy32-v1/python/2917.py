"""2917. Find the K-or of an Array (Easy).

Specification: https://leetcode.com/problems/find-the-k-or-of-an-array/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(31*n) time, O(1) space; the declared domain uses bits zero to thirty."""
    result = 0
    for bit in range(31):
        mask = 1 << bit
        count = 0
        for value in nums:
            if value & mask:
                count += 1
        if count >= k:
            result += mask
    return result


class Solution:
    def findKOr(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
