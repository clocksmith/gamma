"""Original frontend 3857 variant; qualification unknown."""

def solve(n):
    return n * (n - 1) // 2


class Solution:
    def minCost(self, n):
        return solve(n)
