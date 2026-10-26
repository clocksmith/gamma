"""2176. Count Equal and Divisible Pairs in an Array (Easy).

Specification: https://leetcode.com/problems/count-equal-and-divisible-pairs-in-an-array/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n^2) time, O(1) space; divisibility applies to indices, not values."""
    result = 0
    for left in range(len(nums)):
        for right in range(left + 1, len(nums)):
            if nums[left] == nums[right] and left * right % k == 0:
                result += 1
    return result


class Solution:
    def countPairs(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
