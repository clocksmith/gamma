"""Hack2Hire 6775decc2c61a9f93e698ba0 (Find Longest Path in DAG) over an INFERRED spec; qualification unknown."""


def solve(edges):
    if not edges:
        return []
    successors = {}
    indegree = {}
    for a, b in edges:
        successors.setdefault(a, []).append(b)
        successors.setdefault(b, [])
        indegree[b] = indegree.get(b, 0) + 1
        indegree.setdefault(a, 0)
    order = [v for v in successors if indegree[v] == 0]
    i = 0
    while i < len(order):
        v = order[i]
        i += 1
        for w in successors[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                order.append(w)
    length = {}
    following = {}
    for v in reversed(order):
        best = 0
        choice = None
        for w in successors[v]:
            candidate = length[w] + 1
            if candidate > best or (candidate == best and w < choice):
                best = candidate
                choice = w
        length[v] = best
        following[v] = choice
    start = None
    for v in successors:
        if start is None or length[v] > length[start] or (length[v] == length[start] and v < start):
            start = v
    path = [start]
    while following[path[-1]] is not None:
        path.append(following[path[-1]])
    return path


class Solution:
    def longestPath(self, edges):
        return solve(edges)
