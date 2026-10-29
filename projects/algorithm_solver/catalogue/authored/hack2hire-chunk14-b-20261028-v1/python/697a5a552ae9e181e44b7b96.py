"""Hack2Hire 697a5a552ae9e181e44b7b96 (Worker-Task Matching with Specialties, variant 1 of 3) over an INFERRED spec; qualification unknown."""

import heapq


def solve(workers, tasks):
    heap = [(0, name, i) for i, name in enumerate(workers)]
    heapq.heapify(heap)
    lists = [[] for _ in workers]
    for task_id, duration in tasks:
        load, name, i = heap[0]
        lists[i].append(task_id)
        heapq.heapreplace(heap, (load + duration, name, i))
    return lists


class Solution:
    def assignTasks(self, workers, tasks):
        return solve(workers, tasks)
