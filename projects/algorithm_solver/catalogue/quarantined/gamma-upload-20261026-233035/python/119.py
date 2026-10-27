"""119. Pascal's Triangle II."""
def solve(rowIndex: int) -> list[int]:
    row = [1] * (rowIndex + 1)
    for index in range(1, rowIndex):
        row[index] = row[index - 1] * (rowIndex - index + 1) // index
    return row

class Solution:
    def getRow(self, rowIndex: int) -> list[int]:
        return solve(rowIndex)
