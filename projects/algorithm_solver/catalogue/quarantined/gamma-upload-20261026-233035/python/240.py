"""240. Search a 2D Matrix II."""
def solve(matrix: list[list[int]], target: int) -> bool:
    row, column = 0, len(matrix[0]) - 1
    while row < len(matrix) and column >= 0:
        value = matrix[row][column]
        if value == target:
            return True
        if value > target:
            column -= 1
        else:
            row += 1
    return False

class Solution:
    def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:
        return solve(matrix, target)
