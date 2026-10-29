"""Hack2Hire 6976fe265ed12b33b05f1134 (Minimum Distance in N-ary Tree, level 2) over an INFERRED spec; qualification unknown."""

def solve(root, groupA, groupB):
    neighbours = {}
    stack = [(root, None)]
    while stack:
        node, par = stack.pop()
        v = node['val']
        adj = [child['val'] for child in node['children']]
        if par is not None:
            adj.append(par)
        neighbours[v] = adj
        for child in node['children']:
            stack.append((child, v))
    targets = set(groupB)
    seen = set(groupA)
    frontier = list(seen)
    dist = 0
    while frontier:
        for v in frontier:
            if v in targets:
                return dist
        following = []
        for v in frontier:
            for w in neighbours[v]:
                if w not in seen:
                    seen.add(w)
                    following.append(w)
        frontier = following
        dist += 1
    return -1


class Solution:
    def minSetDistance(self, root, groupA, groupB):
        return solve(root, groupA, groupB)
