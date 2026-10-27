"""207. Course Schedule."""
from collections import deque

def solve(numCourses: int, prerequisites: list[list[int]]) -> bool:
    edges = [[] for _ in range(numCourses)]
    degree = [0] * numCourses
    for course, requirement in prerequisites:
        edges[requirement].append(course)
        degree[course] += 1
    queue = deque(index for index, value in enumerate(degree) if value == 0)
    completed = 0
    while queue:
        course = queue.popleft()
        completed += 1
        for following in edges[course]:
            degree[following] -= 1
            if degree[following] == 0:
                queue.append(following)
    return completed == numCourses

class Solution:
    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        return solve(numCourses, prerequisites)
