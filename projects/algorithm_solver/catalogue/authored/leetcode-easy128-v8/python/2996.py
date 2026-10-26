"""2996. Smallest Missing Integer Greater Than Sequential Prefix Sum (Easy).

Specification: https://leetcode.com/problems/smallest-missing-integer-greater-than-sequential-prefix-sum/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; start from the maximal sequential prefix sum and skip present values."""
    candidate = nums[0]
    index = 1
    while index < len(nums) and nums[index] == nums[index - 1] + 1:
        candidate += nums[index]
        index += 1
    present = set(nums)
    while candidate in present:
        candidate += 1
    return candidate


class Solution:
    def missingInteger(self, nums: list[int]) -> int:
        return solve(nums)
