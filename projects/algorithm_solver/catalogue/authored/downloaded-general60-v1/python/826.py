"""826. Most Profit Assigning Work (Medium).

Specification: https://leetcode.com/problems/most-profit-assigning-work/description/
"""


def solve(difficulty: list[int], profit: list[int], worker: list[int]) -> int:
    jobs = sorted(zip(difficulty, profit))
    sorted_workers = sorted(worker)
    best = 0
    job_index = 0
    total = 0
    for ability in sorted_workers:
        while job_index < len(jobs) and jobs[job_index][0] <= ability:
            best = max(best, jobs[job_index][1])
            job_index += 1
        total += best
    return total


class Solution:
    def maxProfitAssignment(self, difficulty: list[int], profit: list[int], worker: list[int]) -> int:
        return solve(difficulty, profit, worker)
