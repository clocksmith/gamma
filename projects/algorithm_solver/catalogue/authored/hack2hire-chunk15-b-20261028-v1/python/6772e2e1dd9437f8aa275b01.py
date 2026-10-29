"""Hack2Hire 6772e2e1dd9437f8aa275b01 (Find Path in N-ary Tree, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def parse(tree):
    values = [tree[0]]
    children = [[]]
    parent = -1
    for x in tree[1:]:
        if x is None:
            parent += 1
        else:
            children[parent].append(len(values))
            values.append(x)
            children.append([])
    return values, children


def solve(tree, path):
    values, children = parse(tree)
    if values[0] != path[0]:
        return False
    frontier = [0]
    for i in range(1, len(path)):
        nxt = []
        for v in frontier:
            for c in children[v]:
                if values[c] == path[i]:
                    nxt.append(c)
        if not nxt:
            return False
        frontier = nxt
    return True


class Solution:
    def pathExists(self, tree, path):
        return solve(tree, path)
