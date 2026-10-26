"""2071. Maximum Number of Tasks You Can Assign."""

from collections import deque


def solve(tasks: list[int], workers: list[int], pills: int, strength: int) -> int:
    """Binary search with a deque assignment check; O((n+m) log(n+m)) time and O(n+m) space. Inputs are preserved."""
    jobs = sorted(tasks)
    people = sorted(workers)

    def feasible(count):
        available = deque()
        cursor = 0
        remaining = pills
        for worker in people[len(people) - count:]:
            while cursor < count and jobs[cursor] <= worker + strength:
                available.append(jobs[cursor])
                cursor += 1
            if not available:
                return False
            if available[0] <= worker:
                available.popleft()
            else:
                if remaining == 0:
                    return False
                remaining -= 1
                available.pop()
        return True

    left, right = 0, min(len(tasks), len(workers))
    while left < right:
        middle = (left + right + 1) // 2
        if feasible(middle):
            left = middle
        else:
            right = middle - 1
    return left


class Solution:
    def maxTaskAssign(self, tasks: list[int], workers: list[int], pills: int, strength: int) -> int:
        return solve(tasks, workers, pills, strength)
