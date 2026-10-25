"""2432. The Employee That Worked on the Longest Task (Easy).

Specification: https://leetcode.com/problems/the-employee-that-worked-on-the-longest-task/description/
"""


def solve(n: int, logs: list[list[int]]) -> int:
    """O(len(logs)) time, O(1) space; use individual tasks, not worker totals."""
    previous_end = 0
    longest_duration = -1
    best_employee = n
    for employee, end in logs:
        duration = end - previous_end
        if duration > longest_duration or (
            duration == longest_duration and employee < best_employee
        ):
            longest_duration = duration
            best_employee = employee
        previous_end = end
    return best_employee


class Solution:
    def hardestWorker(self, n: int, logs: list[list[int]]) -> int:
        return solve(n, logs)
