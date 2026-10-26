"""2974. Minimum Number Game (Easy).

Specification: https://leetcode.com/problems/minimum-number-game/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n log n) time, O(n) space; sort a copy and swap adjacent pairs."""
    result = sorted(nums)
    for index in range(0, len(result), 2):
        result[index], result[index + 1] = result[index + 1], result[index]
    return result


class Solution:
    def numberGame(self, nums: list[int]) -> list[int]:
        return solve(nums)
