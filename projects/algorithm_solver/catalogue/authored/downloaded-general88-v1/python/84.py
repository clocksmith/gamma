"""84. Largest Rectangle in Histogram (Hard).

Specification: https://leetcode.com/problems/largest-rectangle-in-histogram/description/
"""


def solve(heights: list[int]) -> int:
    stack = []
    best = 0
    extended = heights + [0]
    for i, value in enumerate(extended):
        while stack and extended[stack[-1]] > value:
            height = extended[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best


class Solution:
    def largestRectangleArea(self, heights: list[int]) -> int:
        return solve(heights)
