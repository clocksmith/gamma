"""Hack2Hire 67cf7ef7aca6a2fa74a72d1f (Load Factor Calculation) over an INFERRED spec; qualification unknown."""


def solve(dependencies, entry):
    index, names = {}, []

    def node(name):
        if name not in index:
            index[name] = len(names)
            names.append(name)
        return index[name]
    node(entry)
    out, indeg = [], []
    for caller, callee in dependencies:
        a, b = node(caller), node(callee)
        while len(out) < len(names):
            out.append([])
            indeg.append(0)
        out[a].append(b)
        indeg[b] += 1
    while len(out) < len(names):
        out.append([])
        indeg.append(0)
    load = [0] * len(names)
    load[index[entry]] = 1
    queue = [v for v in range(len(names)) if indeg[v] == 0]
    head = 0
    while head < len(queue):
        v = queue[head]
        head += 1
        for w in out[v]:
            load[w] += load[v]
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return [[name, load[index[name]]] for name in sorted(names)]


class Solution:
    def loadFactors(self, dependencies, entry):
        return solve(dependencies, entry)
