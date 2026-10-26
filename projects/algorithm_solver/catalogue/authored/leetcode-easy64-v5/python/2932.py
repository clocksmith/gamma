"""2932. Maximum Strong Pair XOR I (Easy).

Specification: https://leetcode.com/problems/maximum-strong-pair-xor-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n^2) time, O(1) auxiliary space; values are at most 100; preserve nums."""
    largest = 0
    for left in range(len(nums)):
        for right in range(left + 1, len(nums)):
            if abs(nums[left] - nums[right]) <= min(nums[left], nums[right]):
                largest = max(largest, nums[left] ^ nums[right])
    return largest


class Solution:
    def maximumStrongPairXor(self, nums: list[int]) -> int:
        return solve(nums)
