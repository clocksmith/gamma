"""210. Course Schedule II (Medium).

Specification: https://leetcode.com/problems/course-schedule-ii/description/
"""


def solve(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    graph = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses
    for course, prerequisite in prerequisites:
        graph[prerequisite].append(course)
        indegree[course] += 1
    queue = [i for i in range(numCourses) if indegree[i] == 0]
    result = []
    while queue:
        course = queue.pop(0)
        result.append(course)
        for nxt in graph[course]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return result if len(result) == numCourses else []


class Solution:
    def findOrder(self, numCourses: int, prerequisites: list[list[int]]) -> list[int]:
        return solve(numCourses, prerequisites)
