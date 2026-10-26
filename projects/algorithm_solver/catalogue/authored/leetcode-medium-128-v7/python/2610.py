"""2610. Convert an Array Into a 2D Array With Conditions: place the jth occurrence of a value in row j."""


def solve(nums: list[int]) -> list[list[int]]:
    """O(n) expected time and O(n) auxiliary space including the result; inputs are read-only."""
    counts = {}
    rows = []
    for value in nums:
        row = counts.get(value, 0)
        if row == len(rows):
            rows.append([])
        rows[row].append(value)
        counts[value] = row + 1
    return rows


class Solution:
    def findMatrix(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
