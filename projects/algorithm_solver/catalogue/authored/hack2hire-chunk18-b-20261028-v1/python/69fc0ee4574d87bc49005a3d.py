"""Hack2Hire 69fc0ee4574d87bc49005a3d (Data Labeling Task Scheduler, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(totalTask, totalModel, totalHuman, k):
    if k > totalHuman or k > totalModel:
        return []
    # least loaded, smallest index first is round robin over the global assignment number q
    out = []
    q = 0
    for t in range(1, totalTask + 1):
        task = 't' + str(t)
        for _ in range(k):
            out.append([task, 'm' + str(q % totalModel + 1), 'h' + str(q % totalHuman + 1)])
            q += 1
    return out


class Solution:
    def scheduleTasks(self, totalTask, totalModel, totalHuman, k):
        return solve(totalTask, totalModel, totalHuman, k)
