"""304. Range Sum Query 2D - Immutable."""
class NumMatrix:
    def __init__(self, matrix: list[list[int]]):
        rows = len(matrix)
        columns = len(matrix[0]) if rows else 0
        self.prefix = [[0] * (columns + 1) for _ in range(rows + 1)]
        for row in range(rows):
            running = 0
            for column in range(columns):
                running += matrix[row][column]
                self.prefix[row + 1][column + 1] = self.prefix[row][column + 1] + running

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        values = self.prefix
        return values[row2 + 1][col2 + 1] - values[row1][col2 + 1] - values[row2 + 1][col1] + values[row1][col1]

def solve(matrix: list[list[int]], queries: list[list[int]]) -> list[int]:
    structure = NumMatrix(matrix)
    return [structure.sumRegion(*query) for query in queries]
