"""308. Range Sum Query 2D - Mutable."""
class NumMatrix:
    def __init__(self, matrix: list[list[int]]):
        self.rows = len(matrix)
        self.columns = len(matrix[0]) if self.rows else 0
        self.values = [[0] * self.columns for _ in range(self.rows)]
        self.tree = [[0] * (self.columns + 1) for _ in range(self.rows + 1)]
        for row in range(self.rows):
            for column in range(self.columns):
                self.update(row, column, matrix[row][column])

    def _add(self, row: int, column: int, difference: int) -> None:
        r = row + 1
        while r <= self.rows:
            c = column + 1
            while c <= self.columns:
                self.tree[r][c] += difference
                c += c & -c
            r += r & -r

    def update(self, row: int, col: int, val: int) -> None:
        difference = val - self.values[row][col]
        self.values[row][col] = val
        self._add(row, col, difference)

    def _prefix(self, row: int, column: int) -> int:
        total = 0
        r = row
        while r:
            c = column
            while c:
                total += self.tree[r][c]
                c -= c & -c
            r -= r & -r
        return total

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        return (self._prefix(row2 + 1, col2 + 1) - self._prefix(row1, col2 + 1)
                - self._prefix(row2 + 1, col1) + self._prefix(row1, col1))

def solve(matrix, operations, arguments):
    structure = NumMatrix(matrix)
    return [getattr(structure, operation)(*values) for operation, values in zip(operations, arguments)]
