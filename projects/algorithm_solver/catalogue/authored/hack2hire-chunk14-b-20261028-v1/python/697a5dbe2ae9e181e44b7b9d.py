"""Hack2Hire 697a5dbe2ae9e181e44b7b9d (Worker-Task Matching with Specialties, variant 2 of 3) over an INFERRED spec; qualification unknown."""

import heapq


def solve(workers, specialties, tasks, taskTypes):
    heaps = {}
    version = [0] * len(workers)
    load = [0] * len(workers)
    for i, name in enumerate(workers):
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
        for other in specialties[i]:
            heapq.heappush(heaps[other], (load[i], workers[i], i, version[i]))
    return lists + [left]


class Solution:
    def assignTasksBySpecialty(self, workers, specialties, tasks, taskTypes):
        return solve(workers, specialties, tasks, taskTypes)
