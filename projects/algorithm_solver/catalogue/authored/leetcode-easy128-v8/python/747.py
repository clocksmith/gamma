"""747. Largest Number At Least Twice of Others (Easy).

Specification: https://leetcode.com/problems/largest-number-at-least-twice-of-others/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; keep the largest and second-largest nonnegative values."""
    largest = second = -1
    answer = -1
    for index, value in enumerate(nums):
        if value > largest:
            second, largest = largest, value
            answer = index
        else:
            second = max(second, value)
    return answer if largest >= 2 * second else -1


class Solution:
    def dominantIndex(self, nums: list[int]) -> int:
        return solve(nums)
