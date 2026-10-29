"""Hack2Hire 67e4adbf50b60b77022f384b (Find Middle Course, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(pairs):
    index, names = {}, []
    for pair in pairs:
        for name in pair:
            if name not in index:
                index[name] = len(names)
                names.append(name)
    n = len(names)
    out = [[] for _ in range(n)]
    indegree = [0] * n
    for a, b in pairs:
        out[index[a]].append(index[b])
        indegree[index[b]] += 1
    order = [v for v in range(n) if indegree[v] == 0]
    up = [0] * n
    for v in order:
        up[v] = 1
    remaining = list(indegree)
    k = 0
    while k < len(order):
        v = order[k]
        k += 1
        for w in out[v]:
            up[w] |= up[v] << 1
            remaining[w] -= 1
            if remaining[w] == 0:
                order.append(w)
    down = [0] * n
    for v in reversed(order):
        if not out[v]:
            down[v] = 1
        for w in out[v]:
            down[v] |= down[w] << 1
    return sorted(names[v] for v in range(n) if up[v] & (down[v] | (down[v] >> 1)))


class Solution:
    def findMiddleCourses(self, pairs):
        return solve(pairs)
