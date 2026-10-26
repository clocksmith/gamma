"""2553. Separate the Digits in an Array (Easy).

Specification: https://leetcode.com/problems/separate-the-digits-in-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(total digits) time and result space; preserve number order and digit order; preserve nums."""
    result = []
    for value in nums:
        for character in str(value):
            result.append(ord(character) - 48)
    return result


class Solution:
    def separateDigits(self, nums: list[int]) -> list[int]:
        return solve(nums)
