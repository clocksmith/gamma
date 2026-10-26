"""1335. Minimum Difficulty of a Job Schedule.

Partition-prefix dynamic programming; O(d*n^2) time and O(n) space. Inputs are preserved.
"""

def solve(jobDifficulty: list[int], d: int) -> int:
    n = len(jobDifficulty)
    if n < d:
        return -1
    costs = [0] + [float('inf')] * n
    for day in range(1, d + 1):
        following = [float('inf')] * (n + 1)
        for end in range(day, n + 1):
            hardest = 0
            for start in range(end - 1, day - 2, -1):
                hardest = max(hardest, jobDifficulty[start])
                following[end] = min(following[end], costs[start] + hardest)
        costs = following
    return costs[n]


class Solution:
    def minDifficulty(self, jobDifficulty: list[int], d: int) -> int:
        return solve(jobDifficulty, d)
