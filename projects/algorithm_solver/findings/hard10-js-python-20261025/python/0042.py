"""42. Trapping Rain Water (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/trapping-rain-water/description/
Canonical API: solve(height); also exposes Solution.trap.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(height: list[int]) -> int:
    left = 0
    right = len(height) - 1
    left_maximum = 0
    right_maximum = 0
    water = 0
    while left < right:
        if height[left] <= height[right]:
            left_maximum = max(left_maximum, height[left])
            water += left_maximum - height[left]
            left += 1
        else:
            right_maximum = max(right_maximum, height[right])
            water += right_maximum - height[right]
            right -= 1
    return water

class Solution:
    def trap(self, height: list[int]) -> int:
        return solve(height)
