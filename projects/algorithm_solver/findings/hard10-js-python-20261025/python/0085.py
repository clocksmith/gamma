"""85. Maximal Rectangle (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/maximal-rectangle/description/
Canonical API: solve(matrix); also exposes Solution.maximalRectangle.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(matrix: list[list[str]]) -> int:
    if not matrix or not matrix[0]:
        return 0
    columns = len(matrix[0])
    heights = [0] * columns
    largest_area = 0
    for row in matrix:
        for column in range(columns):
            heights[column] = heights[column] + 1 if row[column] == "1" else 0
        stack = []
        for right in range(columns + 1):
            current_height = heights[right] if right < columns else 0
            while stack and heights[stack[-1]] > current_height:
                rectangle_height = heights[stack.pop()]
                left = stack[-1] + 1 if stack else 0
                largest_area = max(largest_area, rectangle_height * (right - left))
            if right < columns:
                stack.append(right)
    return largest_area

class Solution:
    def maximalRectangle(self, matrix: list[list[str]]) -> int:
        return solve(matrix)
