"""3173. Bitwise OR of Adjacent Elements (Easy).

Specification: https://leetcode.com/problems/bitwise-or-of-adjacent-elements/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time, O(n) result space; values are in [0, 100], so bitwise arithmetic is exact."""
    result = []
    for index in range(len(nums) - 1):
        result.append(nums[index] | nums[index + 1])
    return result


class Solution:
    def orArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
