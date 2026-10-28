"""621. Task Scheduler (Medium).

Specification: https://leetcode.com/problems/task-scheduler/description/
"""


def solve(tasks: list[str], n: int) -> int:
    counts = {}
    for task in tasks:
        counts[task] = counts.get(task, 0) + 1
    max_count = max(counts.values())
    num_max = sum(1 for count in counts.values() if count == max_count)
    return max(len(tasks), (max_count - 1) * (n + 1) + num_max)


class Solution:
    def leastInterval(self, tasks: list[str], n: int) -> int:
        return solve(tasks, n)
