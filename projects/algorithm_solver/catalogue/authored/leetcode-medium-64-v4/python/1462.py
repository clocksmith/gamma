"""1462. Course Schedule IV: compute transitive reachability once before answering prerequisite queries."""


def solve(numCourses: int, prerequisites: list[list[int]], queries: list[list[int]]) -> list[bool]:
    """O(v^3 + q) time and O(v^2) auxiliary space; inputs are read-only."""
    reachable = [[False] * numCourses for _ in range(numCourses)]
    for first, second in prerequisites:
        reachable[first][second] = True
    for middle in range(numCourses):
        for first in range(numCourses):
            if reachable[first][middle]:
                for second in range(numCourses):
                    if reachable[middle][second]:
                        reachable[first][second] = True
    return [reachable[first][second] for first, second in queries]


class Solution:
    def checkIfPrerequisite(self, numCourses: int, prerequisites: list[list[int]], queries: list[list[int]]) -> list[bool]:
        return solve(numCourses, prerequisites, queries)
