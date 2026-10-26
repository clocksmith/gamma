"""1504. Count Submatrices With All Ones: sum histogram subarray minima with a counted monotonic stack."""


def solve(mat: list[list[int]]) -> int:
    """O(rows * columns) time and O(columns) auxiliary space; inputs are read-only."""
    heights = [0] * len(mat[0])
    answer = 0
    for row in mat:
        stack = []
        ending_here = 0
        for column, value in enumerate(row):
            heights[column] = heights[column] + 1 if value else 0
            height = heights[column]
            width = 1
            while stack and stack[-1][0] >= height:
                old_height, old_width = stack.pop()
                ending_here -= old_height * old_width
                width += old_width
            stack.append((height, width))
            ending_here += height * width
            answer += ending_here
    return answer


class Solution:
    def numSubmat(self, mat: list[list[int]]) -> int:
        return solve(mat)
