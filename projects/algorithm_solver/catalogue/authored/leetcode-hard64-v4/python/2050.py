"""2050. Parallel Courses III."""

from collections import deque


def solve(n: int, relations: list[list[int]], time: list[int]) -> int:
    """Longest prerequisite path in a DAG; O(V+E) time and space. Inputs are preserved."""
    neighbors = [[] for _ in range(n)]
    incoming = [0] * n
    for first, second in relations:
        neighbors[first - 1].append(second - 1)
        incoming[second - 1] += 1
    finish = list(time)
    queue = deque(node for node in range(n) if incoming[node] == 0)
    while queue:
        node = queue.popleft()
        for target in neighbors[node]:
            finish[target] = max(finish[target], finish[node] + time[target])
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    return max(finish)


class Solution:
    def minimumTime(self, n: int, relations: list[list[int]], time: list[int]) -> int:
        return solve(n, relations, time)
