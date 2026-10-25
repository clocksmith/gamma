"""1074. Number of Submatrices That Sum to Target (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/number-of-submatrices-that-sum-to-target/description/
Canonical API: solve(matrix, target); also exposes Solution.numSubmatrixSumTarget.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(matrix: list[list[int]], target: int) -> int:
    if not matrix or not matrix[0]:
        return 0
    rows = len(matrix)
    columns = len(matrix[0])
    pair_rows = rows <= columns
    boundary_count = min(rows, columns)
    line_length = max(rows, columns)
    total = 0

    for start in range(boundary_count):
        line = [0] * line_length
        for end in range(start, boundary_count):
            for position in range(line_length):
                line[position] += (
                    matrix[end][position] if pair_rows else matrix[position][end]
                )
            frequencies = {0: 1}
            prefix = 0
            for value in line:
                prefix += value
                total += frequencies.get(prefix - target, 0)
                frequencies[prefix] = frequencies.get(prefix, 0) + 1
    return total

class Solution:
    def numSubmatrixSumTarget(self, matrix: list[list[int]], target: int) -> int:
        return solve(matrix, target)
