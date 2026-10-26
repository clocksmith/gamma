"""2589. Minimum Time to Complete All Tasks. Schedule latest unused instants using a Fenwick tree and predecessor links."""


def solve(tasks: list[list[int]]) -> int:
    """O(n log n+(n+T) log(T+1)) time and O(n+T) space, T=max(end). Inputs are preserved."""
    limit = max(task[1] for task in tasks) + 2
    tree = [0] * limit
    parent = list(range(limit))

    def prefix(index):
        result = 0
        while index > 0:
            result += tree[index]
            index -= index & -index
        return result

    def activate(index):
        while index < limit:
            tree[index] += 1
            index += index & -index

    def available(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    answer = 0
    for start, end, duration in sorted(tasks, key=lambda task: task[1]):
        missing = duration - (prefix(end + 1) - prefix(start))
        while missing > 0:
            index = available(end + 1)
            activate(index)
            parent[index] = available(index - 1)
            missing -= 1
            answer += 1
    return answer


class Solution:
    def findMinimumTime(self, tasks: list[list[int]]) -> int:
        return solve(tasks)
