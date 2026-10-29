"""Hack2Hire 697a5dbf2ae9e181e44b7b9e (Worker-Task Matching with Specialties, variant 3 of 3) over an INFERRED spec; qualification unknown."""

import heapq


def solve(workers, specialties, maxTasks, tasks, taskTypes):
    heaps = {}
    version = [0] * len(workers)
    load = [0] * len(workers)
    for i, name in enumerate(workers):
        if maxTasks[i] > 0:
            for kind in specialties[i]:
                heaps.setdefault(kind, []).append((0, name, i, 0))
    for heap in heaps.values():
        heapq.heapify(heap)
    lists = [[] for _ in workers]
    left = []
    for (task_id, duration), kind in zip(tasks, taskTypes):
        heap = heaps.get(kind)
        while heap and heap[0][3] != version[heap[0][2]]:
            heapq.heappop(heap)
        if not heap:
            left.append(task_id)
            continue
        i = heap[0][2]
        lists[i].append(task_id)
        load[i] += duration
        version[i] += 1
        if len(lists[i]) < maxTasks[i]:
            for other in specialties[i]:
                heapq.heappush(heaps[other], (load[i], workers[i], i, version[i]))
    return lists + [left]


class Solution:
    def assignTasksWithLimits(self, workers, specialties, maxTasks, tasks, taskTypes):
        return solve(workers, specialties, maxTasks, tasks, taskTypes)
