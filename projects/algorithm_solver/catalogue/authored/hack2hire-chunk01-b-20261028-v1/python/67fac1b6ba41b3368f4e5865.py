"""Hack2Hire 67fac1b6ba41b3368f4e5865 (Find Destination Node, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""
from collections import deque


def solve(edges, start):
    adjacency = {}
    for u, v in edges:
        adjacency.setdefault(u, []).append(v)
    seen, queue, sinks = {start}, deque([start]), []
    while queue:
        node = queue.popleft()
        if node not in adjacency:
            sinks.append(node)
            continue
        for nxt in adjacency[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return sorted(sinks)


class Solution:
    def findDestinationNodes(self, edges, start):
        return solve(edges, start)
