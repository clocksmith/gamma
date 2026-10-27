"""453. Minimum Moves to Equal Array Elements. Incrementing n-1 entries is equivalent to decrementing one relative value."""

def solve(nums: list[int]) -> int:
    minimum = min(nums)
    return sum(value - minimum for value in nums)


class Solution:
    def minMoves(self, nums: list[int]) -> int:
        return solve(nums)
