"""Hack2Hire 693903ffb03e15724c2174c5 (Level Order Task Scheduling) over an INFERRED spec; qualification unknown."""


def solve(tasks, dependencies):
    indegree = {t: 0 for t in tasks}
    successors = {t: [] for t in tasks}
    for before, after in dependencies:
        successors[before].append(after)
        indegree[after] += 1
    frontier = sorted(t for t in tasks if indegree[t] == 0)
    levels = []
    emitted = 0
    while frontier:
        levels.append(frontier)
        emitted += len(frontier)
        following = []
        for t in frontier:
            for s in successors[t]:
                indegree[s] -= 1
                if indegree[s] == 0:
                    following.append(s)
        following.sort()
        frontier = following
    return levels if emitted == len(tasks) else []


class Solution:
    def scheduleByLevels(self, tasks, dependencies):
        return solve(tasks, dependencies)
