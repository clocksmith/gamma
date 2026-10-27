"""210. Course Schedule II."""
from collections import deque

def solve(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    edges = [[] for _ in range(numCourses)]
    degree = [0] * numCourses
    for course, requirement in prerequisites:
        edges[requirement].append(course)
        degree[course] += 1
    queue = deque(index for index, value in enumerate(degree) if value == 0)
    order = []
    while queue:
        course = queue.popleft()
        order.append(course)
        for following in edges[course]:
            degree[following] -= 1
            if degree[following] == 0:
                queue.append(following)
    return order if len(order) == numCourses else []

class Solution:
    def findOrder(self, numCourses: int, prerequisites: list[list[int]]) -> list[int]:
        return solve(numCourses, prerequisites)
