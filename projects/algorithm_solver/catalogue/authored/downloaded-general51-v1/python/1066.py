"""1066. Campus Bikes II (Medium).

Specification: https://leetcode.com/problems/campus-bikes-ii/description/
"""


def solve(workers: list[list[int]], bikes: list[list[int]]) -> int:
    memo = {}

    def dp(worker_index, used_mask):
        if worker_index == len(workers):
            return 0
        key = (worker_index, used_mask)
        if key in memo:
            return memo[key]
        best = float('inf')
        for b, bike in enumerate(bikes):
            if not (used_mask & (1 << b)):
                distance = abs(workers[worker_index][0] - bike[0]) + abs(workers[worker_index][1] - bike[1])
                best = min(best, distance + dp(worker_index + 1, used_mask | (1 << b)))
        memo[key] = best
        return best

    return dp(0, 0)


class Solution:
    def assignBikes(self, workers: list[list[int]], bikes: list[list[int]]) -> int:
        return solve(workers, bikes)
