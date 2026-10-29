"""Hack2Hire 6a038c052608e589a944ac93 (Highest Earning Experience Tracker) over an INFERRED spec; qualification unknown."""

import heapq


def solve(operations, experiences, deltas):
    totals = {}
    heap = []
    out = []
    for op, name, delta in zip(operations, experiences, deltas):
        if op == 'U':
            total = totals.get(name, 0) + delta
            totals[name] = total
            heapq.heappush(heap, (-total, name))
        else:
            while heap and totals[heap[0][1]] != -heap[0][0]:
                heapq.heappop(heap)
            out.append(heap[0][1] if heap else '')
    return out


class Solution:
    def highestEarningExperiences(self, operations, experiences, deltas):
        return solve(operations, experiences, deltas)
