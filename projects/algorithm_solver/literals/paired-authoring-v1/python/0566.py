class Solution:
    def matrixReshape(self, mat: list[list[int]], r: int, c: int) -> list[list[int]]:
        if len(mat) * len(mat[0]) != r * c:
            return mat

        result = [[0] * c for _ in range(r)]
        output_row = 0
        output_column = 0
        for row in mat:
            for value in row:
                result[output_row][output_column] = value
                output_column += 1
                if output_column == c:
                    output_column = 0
                    output_row += 1
        return result
