"""Hack2Hire 696eb8a4920c39311a3992be (Minimum Distance in N-ary Tree, level 1) over an INFERRED spec; qualification unknown."""

def solve(root, p, q):
    parent, depth = {}, {}
    stack = [(root, None, 0)]
    while stack:
        node, par, d = stack.pop()
        v = node['val']
        parent[v] = par
        depth[v] = d
        for child in node['children']:
            stack.append((child, v, d + 1))
    x, y, dist = p, q, 0
    while depth[x] > depth[y]:
        x = parent[x]
        dist += 1
    while depth[y] > depth[x]:
        y = parent[y]
        dist += 1
    while x != y:
        x = parent[x]
        y = parent[y]
        dist += 2
    return dist


class Solution:
    def treeDistance(self, root, p, q):
        return solve(root, p, q)
