"""3683. Earliest Time to Finish One Task (Easy).

Specification: https://leetcode.com/problems/earliest-time-to-finish-one-task/description/
"""


def solve(tasks: list[list[int]]) -> int:
    """O(n) time, O(1) auxiliary space; preserve tasks and its rows."""
    earliest = float('inf')
    for start, duration in tasks:
        earliest = min(earliest, start + duration)
    return earliest


class Solution:
    def earliestTime(self, tasks: list[list[int]]) -> int:
        return solve(tasks)
