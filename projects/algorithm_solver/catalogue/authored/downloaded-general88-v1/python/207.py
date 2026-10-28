"""207. Course Schedule (Medium).

Specification: https://leetcode.com/problems/course-schedule/description/
"""


def solve(numCourses: int, prerequisites: list[list[int]]) -> bool:
    graph = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses
    for course, prerequisite in prerequisites:
        graph[prerequisite].append(course)
        indegree[course] += 1
    queue = [i for i in range(numCourses) if indegree[i] == 0]
    finished = 0
    while queue:
        course = queue.pop(0)
        finished += 1
        for nxt in graph[course]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return finished == numCourses


class Solution:
    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        return solve(numCourses, prerequisites)
