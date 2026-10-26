"""1701. Average Waiting Time: advance the single chef clock and sum each customer completion delay."""


def solve(customers: list[list[int]]) -> float:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    finished = total_wait = 0
    for arrival, preparation in customers:
        finished = max(finished, arrival) + preparation
        total_wait += finished - arrival
    return total_wait / len(customers)


class Solution:
    def averageWaitingTime(self, customers: list[list[int]]) -> float:
        return solve(customers)
