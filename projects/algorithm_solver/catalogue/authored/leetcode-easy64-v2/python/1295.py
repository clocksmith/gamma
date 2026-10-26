"""1295. Find Numbers with Even Number of Digits (Easy).

Specification: https://leetcode.com/problems/find-numbers-with-even-number-of-digits/description/
"""


def solve(nums: list[int]) -> int:
    """O(n * d) time, O(d) temporary space; preserve nums. d is the digit bound."""
    result = 0
    for value in nums:
        if len(str(value)) % 2 == 0:
            result += 1
    return result


class Solution:
    def findNumbers(self, nums: list[int]) -> int:
        return solve(nums)
