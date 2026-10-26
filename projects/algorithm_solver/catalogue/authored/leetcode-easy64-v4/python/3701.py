"""3701. Compute Alternating Sum (Easy).

Specification: https://leetcode.com/problems/compute-alternating-sum/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; preserve nums."""
    result = 0
    sign = 1
    for value in nums:
        result += sign * value
        sign = -sign
    return result


class Solution:
    def alternatingSum(self, nums: list[int]) -> int:
        return solve(nums)
