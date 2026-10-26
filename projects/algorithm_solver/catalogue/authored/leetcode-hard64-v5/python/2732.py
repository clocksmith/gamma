"""2732. Find a Good Subset of the Matrix. Find a zero row or two disjoint row masks in the at-most-five-column domain."""


def solve(grid: list[list[int]]) -> list[int]:
    """O(m*n+4^n) time and O(2^n) space for n<=5. Inputs are preserved."""
    first = {}
    for index, row in enumerate(grid):
        mask = 0
        for column, value in enumerate(row):
            mask |= value << column
        if mask == 0:
            return [index]
        first.setdefault(mask, index)
    masks = list(first)
    for index, mask in enumerate(masks):
        for other in masks[index + 1:]:
            if mask & other == 0:
                return sorted((first[mask], first[other]))
    return []


class Solution:
    def goodSubsetofBinaryMatrix(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
