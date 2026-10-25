"""84. Largest Rectangle in Histogram (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/largest-rectangle-in-histogram/description/
Canonical API: solve(heights); also exposes Solution.largestRectangleArea.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(heights: list[int]) -> int:
    stack = []
    largest_area = 0
    for right in range(len(heights) + 1):
        current_height = heights[right] if right < len(heights) else 0
        while stack and heights[stack[-1]] > current_height:
            rectangle_height = heights[stack.pop()]
            left = stack[-1] + 1 if stack else 0
            largest_area = max(largest_area, rectangle_height * (right - left))
        if right < len(heights):
            stack.append(right)
    return largest_area

class Solution:
    def largestRectangleArea(self, heights: list[int]) -> int:
        return solve(heights)
