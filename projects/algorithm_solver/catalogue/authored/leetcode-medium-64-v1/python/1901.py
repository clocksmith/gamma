"""1901. Find a Peak Element II: binary search columns using the maximum entry in each inspected column."""


def solve(mat: list[list[int]]) -> list[int]:
    """O(rows * log(columns + 1)) time and O(1) auxiliary space; inputs are read-only."""
    rows, columns = len(mat), len(mat[0])
    low, high = 0, columns - 1
    while low <= high:
        middle = (low + high) // 2
        row = max(range(rows), key=lambda index: mat[index][middle])
        value = mat[row][middle]
        left = mat[row][middle - 1] if middle else float('-inf')
        right = mat[row][middle + 1] if middle + 1 < columns else float('-inf')
        if value > left and value > right:
            return [row, middle]
        if left > value:
            high = middle - 1
        else:
            low = middle + 1
    return []


class Solution:
    def findPeakGrid(self, mat: list[list[int]]) -> list[int]:
        return solve(mat)
