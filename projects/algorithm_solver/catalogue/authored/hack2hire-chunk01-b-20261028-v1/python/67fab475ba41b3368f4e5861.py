"""Hack2Hire 67fab475ba41b3368f4e5861 (Find Destination Node, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(edges, start):
    successor = {u: v for u, v in edges}
    seen, node = set(), start
    while node in successor:
        if node in seen:
            return -1
        seen.add(node)
        node = successor[node]
    return node


class Solution:
    def findDestinationNode(self, edges, start):
        return solve(edges, start)
