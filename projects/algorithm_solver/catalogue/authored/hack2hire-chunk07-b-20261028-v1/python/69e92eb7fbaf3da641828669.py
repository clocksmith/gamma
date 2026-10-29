"""Hack2Hire 69e92eb7fbaf3da641828669 (Palindromic Storage Paths) over an INFERRED spec; qualification unknown."""

def solve(arr, treeFrom, treeTo, queries):
    n = len(arr)
    adj = [[] for _ in range(n)]
    for u, v in zip(treeFrom, treeTo):
        adj[u].append(v)
        adj[v].append(u)
    wanted = [False] * n
    for q in queries:
        wanted[q] = True
    answer = [0] * n
    counts = {0: 1}  # prefix masks P[parent(v)] for v on the current root path; 0 stands for v = root
    stack = [(0, -1, 0, False)]
    while stack:
        u, parent, mask, leaving = stack.pop()
        if leaving:
            counts[mask] -= 1
            continue
        mask ^= 1 << (ord(arr[u]) - 97)
        if wanted[u]:
            total = counts.get(mask, 0)
            for bit in range(26):
                total += counts.get(mask ^ (1 << bit), 0)
            answer[u] = total
        counts[mask] = counts.get(mask, 0) + 1
        stack.append((u, parent, mask, True))
        for v in adj[u]:
            if v != parent:
                stack.append((v, u, mask, False))
    return [answer[q] for q in queries]


class Solution:
    def palindromicPaths(self, arr, treeFrom, treeTo, queries):
        return solve(arr, treeFrom, treeTo, queries)
