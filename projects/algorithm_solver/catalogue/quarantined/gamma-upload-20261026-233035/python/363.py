"""363. Max Sum of Rectangle No Larger Than K."""
from bisect import bisect_left, insort

def solve(matrix: list[list[int]], k: int) -> int:
    rows, columns = len(matrix), len(matrix[0])
    if rows > columns:
        matrix = [list(row) for row in zip(*matrix)]
        rows, columns = columns, rows
    best = float('-inf')
    for top in range(rows):
        sums = [0] * columns
        for bottom in range(top, rows):
            for column in range(columns):
                sums[column] += matrix[bottom][column]
            prefix = 0
            prefixes = [0]
            for value in sums:
                prefix += value
                index = bisect_left(prefixes, prefix - k)
                if index < len(prefixes):
                    best = max(best, prefix - prefixes[index])
                insort(prefixes, prefix)
            if best == k:
                return k
    return best

class Solution:
    def maxSumSubmatrix(self, matrix, k):
        return solve(matrix, k)
