"""2148. Count Elements With Strictly Smaller and Greater Elements (Easy).

Specification: https://leetcode.com/problems/count-elements-with-strictly-smaller-and-greater-elements/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; count values strictly between the extrema; preserve nums."""
    smallest = min(nums)
    largest = max(nums)
    return sum(smallest < value < largest for value in nums)


class Solution:
    def countElements(self, nums: list[int]) -> int:
        return solve(nums)
