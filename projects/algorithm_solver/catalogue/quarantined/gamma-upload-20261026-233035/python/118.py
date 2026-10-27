"""118. Pascal's Triangle."""
def solve(numRows: int) -> list[list[int]]:
    result = []
    for row in range(numRows):
        values = [1] * (row + 1)
        for column in range(1, row):
            values[column] = result[row - 1][column - 1] + result[row - 1][column]
        result.append(values)
    return result

class Solution:
    def generate(self, numRows: int) -> list[list[int]]:
        return solve(numRows)
