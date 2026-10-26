"""1738. Find Kth Largest XOR Coordinate Value: accumulate column-prefix XOR values and sort the coordinate results."""


def solve(matrix: list[list[int]], k: int) -> int:
    """O(rows * columns * log(rows * columns + 1)) time and O(rows * columns) auxiliary space; inputs are read-only."""
    above = [0] * len(matrix[0])
    values = []
    for row in matrix:
        row_xor = 0
        for column, value in enumerate(row):
            row_xor ^= value
            above[column] ^= row_xor
            values.append(above[column])
    values.sort(reverse=True)
    return values[k - 1]


class Solution:
    def kthLargestValue(self, matrix: list[list[int]], k: int) -> int:
        return solve(matrix, k)
