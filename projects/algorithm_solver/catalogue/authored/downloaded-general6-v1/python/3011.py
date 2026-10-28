"""3011. Find if Array Can Be Sorted (Medium).

Specification: https://leetcode.com/problems/find-if-array-can-be-sorted/description/
"""


def count_bits(x: int) -> int:
    return bin(x).count("1")


def solve(nums: list[int]) -> bool:
    previous_max = float("-inf")
    i = 0
    while i < len(nums):
        bits = count_bits(nums[i])
        group_min = nums[i]
        group_max = nums[i]
        j = i + 1
        while j < len(nums) and count_bits(nums[j]) == bits:
            group_min = min(group_min, nums[j])
            group_max = max(group_max, nums[j])
            j += 1
        if previous_max > group_min:
            return False
        previous_max = group_max
        i = j
    return True


class Solution:
    def canSortArray(self, nums: list[int]) -> bool:
        return solve(nums)
