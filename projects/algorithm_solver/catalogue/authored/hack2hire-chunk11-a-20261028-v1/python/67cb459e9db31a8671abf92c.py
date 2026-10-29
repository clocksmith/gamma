"""Hack2Hire 67cb459e9db31a8671abf92c (Find Lowest Common Manager) over an INFERRED spec; qualification unknown."""


def solve(hierarchy, employee1, employee2):
    reports = {name: direct for name, direct in hierarchy}
    root = hierarchy[0][0]
    parent, depth, queue = {root: None}, {root: 0}, [root]
    i = 0
    while i < len(queue):  # iterative breadth-first pass: the tree may be 1e5 deep
        x = queue[i]
        i += 1
        for child in reports[x]:
            parent[child] = x
            depth[child] = depth[x] + 1
            queue.append(child)
    a, b = employee1, employee2
    while depth[a] > depth[b]:
        a = parent[a]
    while depth[b] > depth[a]:
        b = parent[b]
    while a != b:
        a, b = parent[a], parent[b]
    return a


class Solution:
    def findLowestCommonManager(self, hierarchy, employee1, employee2):
        return solve(hierarchy, employee1, employee2)
