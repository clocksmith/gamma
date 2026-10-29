"""Hack2Hire 67fda0b6d2adf72ba62b0ed9 (Gift Delivery Scheduler) over an INFERRED spec; qualification unknown."""


def solve(intervals, n):
    # by_start[s][e]: recipients available from hour s until hour e (e <= 17)
    by_start = [[0] * 18 for _ in range(18)]
    for start, end in intervals:
        by_start[start][end] += 1
    waiting = [0] * 18  # waiting recipients by end hour: a bucket priority queue
    served = 0
    for hour in range(9, 17):
        for end in range(hour + 1, 18):
            waiting[end] += by_start[hour][end]
        waiting[hour] = 0  # availability ended
        capacity = n
        for end in range(hour + 1, 18):
            if capacity == 0:
                break
            take = min(capacity, waiting[end])
            waiting[end] -= take
            capacity -= take
            served += take
    return served


class Solution:
    def maxDeliveries(self, intervals, n):
        return solve(intervals, n)
