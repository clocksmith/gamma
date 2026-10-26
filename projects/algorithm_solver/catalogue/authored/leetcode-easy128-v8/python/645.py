"""645. Set Mismatch (Easy).

Specification: https://leetcode.com/problems/set-mismatch/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; count occurrences and return duplicate then missing."""
    counts = [0] * (len(nums) + 1)
    for value in nums:
        counts[value] += 1
    duplicate = missing = 0
    for value in range(1, len(nums) + 1):
        if counts[value] == 2:
            duplicate = value
        elif counts[value] == 0:
            missing = value
    return [duplicate, missing]


class Solution:
    def findErrorNums(self, nums: list[int]) -> list[int]:
        return solve(nums)
