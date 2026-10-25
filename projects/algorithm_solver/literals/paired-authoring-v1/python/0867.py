class Solution:
    def transpose(self, matrix: list[list[int]]) -> list[list[int]]:
        rows = len(matrix)
        columns = len(matrix[0]) if rows > 0 else 0
        output = [[0] * rows for _ in range(columns)]
        for row in range(rows):
            for column in range(columns):
                output[column][row] = matrix[row][column]
        return output
