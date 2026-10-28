"""Original frontend 3937 variant; qualification unknown."""

def solve(nums, k):
    costs = [[0] * k for _ in range(2)]
    for i, value in enumerate(nums):
        current = value % k
        for target in range(k):
            difference = abs(current - target)
            costs[i % 2][target] += min(difference, k - difference)
    return min(costs[0][x] + costs[1][y] for x in range(k) for y in range(k) if x != y)


class Solution:
    def minOperations(self, nums, k):
        return solve(nums, k)
