"""1376. Time Needed to Inform All Employees: propagate message arrival times through an iterative hierarchy traversal."""


def solve(n: int, headID: int, manager: list[int], informTime: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    children = [[] for _ in range(n)]
    for employee, parent in enumerate(manager):
        if parent != -1:
            children[parent].append(employee)
    stack = [(headID, 0)]
    latest = 0
    while stack:
        employee, arrival = stack.pop()
        latest = max(latest, arrival)
        following = arrival + informTime[employee]
        for child in children[employee]:
            stack.append((child, following))
    return latest


class Solution:
    def numOfMinutes(self, n: int, headID: int, manager: list[int], informTime: list[int]) -> int:
        return solve(n, headID, manager, informTime)
