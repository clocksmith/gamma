"""Hack2Hire 67896bfb11318cc872dd83ea (Group Elements by Shared Properties) over an INFERRED spec; qualification unknown."""


def solve(elements):
    n = len(elements)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for position in (1, 2, 3):
        first = {}
        for i in range(n):
            value = elements[i][position]
            if value in first:
                a, b = find(first[value]), find(i)
                if a != b:
                    parent[a] = b
            else:
                first[value] = i
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(elements[i][0])
    out = []
    for ids in groups.values():
        ids.sort()
        out.append(ids)
    out.sort(key=lambda g: g[0])
    return out


class Solution:
    def groupElements(self, elements):
        return solve(elements)
