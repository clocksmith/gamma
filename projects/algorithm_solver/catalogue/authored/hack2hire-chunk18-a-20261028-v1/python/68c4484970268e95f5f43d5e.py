"""Hack2Hire 68c4484970268e95f5f43d5e (Minimum Vertices to Traverse Directed Graph) over an INFERRED spec; qualification unknown."""


def solve(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    index = [-1] * n
    low = [0] * n
    pointer = [0] * n
    on_stack = [False] * n
    comp = [-1] * n
    stack = []
    counter = 0
    components = 0
    for s in range(n):
        if index[s] != -1:
            continue
        index[s] = low[s] = counter
        counter += 1
        stack.append(s)
        on_stack[s] = True
        work = [s]
        while work:
            v = work[-1]
            if pointer[v] < len(adj[v]):
                w = adj[v][pointer[v]]
                pointer[v] += 1
                if index[w] == -1:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack[w] = True
                    work.append(w)
                elif on_stack[w] and index[w] < low[v]:
                    low[v] = index[w]
                continue
            work.pop()
            if work and low[v] < low[work[-1]]:
                low[work[-1]] = low[v]
            if low[v] == index[v]:
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    comp[w] = components
                    if w == v:
                        break
                components += 1
    entered = [False] * components
    for u, v in edges:
        if comp[u] != comp[v]:
            entered[comp[v]] = True
    return entered.count(False)


class Solution:
    def minActivatedServers(self, n, edges):
        return solve(n, edges)
