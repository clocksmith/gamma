"""448. Find All Numbers Disappeared in an Array (Easy).

Specification: https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; preserve nums and return missing values in ascending order."""
    present = [False] * (len(nums) + 1)
    for value in nums:
        present[value] = True
    return [value for value in range(1, len(nums) + 1) if not present[value]]


class Solution:
    def findDisappearedNumbers(self, nums: list[int]) -> list[int]:
        return solve(nums)
