"""3038. Maximum Number of Operations With the Same Score I (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-operations-with-the-same-score-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; inspect consecutive disjoint pairs without deleting inputs."""
    score = nums[0] + nums[1]
    operations = 0
    for index in range(0, len(nums) - 1, 2):
        if nums[index] + nums[index + 1] != score:
            break
        operations += 1
    return operations


class Solution:
    def maxOperations(self, nums: list[int]) -> int:
        return solve(nums)
