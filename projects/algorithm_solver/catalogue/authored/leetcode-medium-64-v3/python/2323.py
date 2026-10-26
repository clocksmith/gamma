"""2323. Find Minimum Time to Finish All Jobs II: match sorted job sizes to sorted worker rates."""


def solve(jobs: list[int], workers: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered_jobs = sorted(jobs)
    ordered_workers = sorted(workers)
    answer = 0
    for job, rate in zip(ordered_jobs, ordered_workers):
        answer = max(answer, (job + rate - 1) // rate)
    return answer


class Solution:
    def minimumTime(self, jobs: list[int], workers: list[int]) -> int:
        return solve(jobs, workers)
