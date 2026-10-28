"""11. Container With Most Water (Medium).

Specification: https://leetcode.com/problems/container-with-most-water/description/
"""


def solve(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        best = max(best, min(height[left], height[right]) * (right - left))
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


class Solution:
    def maxArea(self, height: list[int]) -> int:
        return solve(height)
