"""169. Majority Element (Easy).

Specification: https://leetcode.com/problems/majority-element/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; Boyer-Moore voting under the guaranteed-majority contract."""
    candidate = 0
    balance = 0
    for value in nums:
        if balance == 0:
            candidate = value
        balance += 1 if value == candidate else -1
    return candidate


class Solution:
    def majorityElement(self, nums: list[int]) -> int:
        return solve(nums)
