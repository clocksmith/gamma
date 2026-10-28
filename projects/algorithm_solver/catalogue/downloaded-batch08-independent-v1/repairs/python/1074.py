"""1074. Number of Submatrices That Sum to Target.

Canonical definition: https://leetcode.com/problems/number-of-submatrices-that-sum-to-target/description/
Separate correct-identity variant; supplied1074 dice source is preserved.
"""


def solve(matrix: list[list[int]], target: int) -> int:
    rows, cols = len(matrix), len(matrix[0])
    answer = 0
    for top in range(rows):
        sums = [0] * cols
        for bottom in range(top, rows):
            for col in range(cols):
                sums[col] += matrix[bottom][col]
            frequencies = {0: 1}
            prefix = 0
            for value in sums:
                prefix += value
                answer += frequencies.get(prefix - target, 0)
                frequencies[prefix] = frequencies.get(prefix, 0) + 1
    return answer


class Solution:
    def numSubmatrixSumTarget(self, matrix: list[list[int]], target: int) -> int:
        return solve(matrix, target)
