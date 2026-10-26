"""3069. Distribute Elements Into Two Arrays I (Easy).

Specification: https://leetcode.com/problems/distribute-elements-into-two-arrays-i/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; return a fresh concatenation and preserve nums."""
    first = [nums[0]]
    second = [nums[1]]
    for index in range(2, len(nums)):
        if first[-1] > second[-1]:
            first.append(nums[index])
        else:
            second.append(nums[index])
    return first + second


class Solution:
    def resultArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
