"""2365. Task Scheduler II: jump directly to each task type's next legal execution day."""


def solve(tasks: list[int], space: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    next_day = {}
    day = 0
    for task in tasks:
        day = max(day + 1, next_day.get(task, 1))
        next_day[task] = day + space + 1
    return day


class Solution:
    def taskSchedulerII(self, tasks: list[int], space: int) -> int:
        return solve(tasks, space)
