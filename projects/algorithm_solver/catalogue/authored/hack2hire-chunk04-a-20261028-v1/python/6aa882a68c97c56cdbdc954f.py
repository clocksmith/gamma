"""Hack2Hire 6aa882a68c97c56cdbdc954f (Uniform Group Spanning Tree) over an INFERRED spec; qualification unknown."""

from heapq import heapify, heappop, heappush


def solve(groups, rank):
    k = len(groups)
    if k == 1:
        return []
    r = int(rank)
    pick = []
    for group in groups:
        r, digit = divmod(r, len(group))
        pick.append(group[digit])
    nodes, owner = [], []
    for g, group in enumerate(groups):
        nodes.extend(group)
        owner.extend([g] * len(group))
    code = []
    for _ in range(k - 2):
        r, position = divmod(r, len(nodes))
        code.append(position)
    degree = [1] * k
    for position in code:
        degree[owner[position]] += 1
    leaves = [g for g in range(k) if degree[g] == 1]
    heapify(leaves)
    edges = []
    for position in code:
        leaf = heappop(leaves)
        degree[leaf] = 0
        edges.append([pick[leaf], nodes[position]])
        g = owner[position]
        degree[g] -= 1
        if degree[g] == 1:
            heappush(leaves, g)
    u, v = sorted(leaves)
    edges.append([pick[u], pick[v]])
    return edges


class Solution:
    def uniformSpanningTree(self, groups, rank):
        return solve(groups, rank)
