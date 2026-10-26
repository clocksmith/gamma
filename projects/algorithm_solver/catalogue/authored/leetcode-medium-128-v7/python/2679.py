"""2679. Sum in a Matrix: sort copied rows and sum the maximum value at each removal rank."""


def solve(nums: list[list[int]]) -> int:
    """O(r * c log(c + 1)) time and O(r * c) auxiliary space; inputs are read-only."""
    ordered = [sorted(row) for row in nums]
    return sum(max(row[column] for row in ordered) for column in range(len(nums[0])))


class Solution:
    def matrixSum(self, nums: list[list[int]]) -> int:
        return solve(nums)
