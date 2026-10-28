"""1558. Minimum Numbers of Function Calls to Make Target Array (Medium).

Specification: https://leetcode.com/problems/minimum-numbers-of-function-calls-to-make-target-array/description/
"""


def solve(nums: list[int]) -> int:
    operations = 0
    values = nums[:]
    while any(v > 0 for v in values):
        odd_count = 0
        for i in range(len(values)):
            if values[i] % 2 == 1:
                values[i] -= 1
                odd_count += 1
        operations += odd_count
        if any(v > 0 for v in values):
            values = [v // 2 for v in values]
            operations += 1
    return operations


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
