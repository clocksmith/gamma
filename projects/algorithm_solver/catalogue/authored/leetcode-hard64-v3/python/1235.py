"""1235. Maximum Profit in Job Scheduling: weighted interval scheduling; O(n log n) time and O(n) space. Inputs are preserved."""

from bisect import bisect_left


def solve(startTime: list[int], endTime: list[int], profit: list[int]) -> int:
    jobs = sorted(zip(startTime, endTime, profit))
    starts = [job[0] for job in jobs]
    best = [0] * (len(jobs) + 1)
    for index in range(len(jobs) - 1, -1, -1):
        _, end, value = jobs[index]
        following = bisect_left(starts, end, index + 1)
        best[index] = max(best[index + 1], value + best[following])
    return best[0]


class Solution:
    def jobScheduling(self, startTime: list[int], endTime: list[int], profit: list[int]) -> int:
        return solve(startTime, endTime, profit)
