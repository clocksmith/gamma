"""1424. Diagonal Traverse II: bucket ragged rows by diagonal and read each bucket bottom-up."""


def solve(nums: list[list[int]]) -> list[int]:
    """O(S) time and O(S) auxiliary space, where S is the total number of elements; inputs are read-only."""
    diagonals = []
    for row, values in enumerate(nums):
        for col, value in enumerate(values):
            diagonal = row + col
            while len(diagonals) <= diagonal:
                diagonals.append([])
            diagonals[diagonal].append(value)
    result = []
    for diagonal in diagonals:
        result.extend(reversed(diagonal))
    return result


class Solution:
    def findDiagonalOrder(self, nums: list[list[int]]) -> list[int]:
        return solve(nums)
