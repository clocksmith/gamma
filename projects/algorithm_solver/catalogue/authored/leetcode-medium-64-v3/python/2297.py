"""2297. Jump Game VIII: relax the next greater-or-equal and next smaller jumps with two monotone stacks."""


def solve(nums: list[int], costs: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    distance = [float('inf')] * len(nums)
    distance[0] = 0
    decreasing = []
    increasing = []
    for index, value in enumerate(nums):
        while decreasing and nums[decreasing[-1]] <= value:
            previous = decreasing.pop()
            distance[index] = min(distance[index], distance[previous] + costs[index])
        while increasing and nums[increasing[-1]] > value:
            previous = increasing.pop()
            distance[index] = min(distance[index], distance[previous] + costs[index])
        decreasing.append(index)
        increasing.append(index)
    return distance[-1]


class Solution:
    def minCost(self, nums: list[int], costs: list[int]) -> int:
        return solve(nums, costs)
