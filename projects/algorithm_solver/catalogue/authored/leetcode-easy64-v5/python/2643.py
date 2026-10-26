"""2643. Row With Maximum Ones (Easy).

Specification: https://leetcode.com/problems/row-with-maximum-ones/description/
"""


def solve(mat: list[list[int]]) -> list[int]:
    """O(r * c) time, O(1) auxiliary space; preserve mat; favor the first row on ties."""
    best_row = 0
    best_count = -1
    for row, values in enumerate(mat):
        count = sum(values)
        if count > best_count:
            best_row = row
            best_count = count
    return [best_row, best_count]


class Solution:
    def rowAndMaximumOnes(self, mat: list[list[int]]) -> list[int]:
        return solve(mat)
