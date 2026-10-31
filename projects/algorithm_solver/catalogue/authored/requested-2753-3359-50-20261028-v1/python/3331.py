"""Original frontend 3331 variant; qualification unknown."""


def solve(parent, s: str):
    n = len(parent)
    children = [[] for _ in range(n)]
    for i in range(1, n):
        children[parent[i]].append(i)
    new_parent = list(parent)
    last_seen = {}

    def dfs_reparent(u: int):
        ch = s[u]
        prev = last_seen.get(ch)
        if prev is not None:
            new_parent[u] = prev
        last_seen[ch] = u
        for v in children[u]:
            dfs_reparent(v)
        if prev is None:
            del last_seen[ch]
        else:
            last_seen[ch] = prev

    dfs_reparent(0)
    new_children = [[] for _ in range(n)]
    for i in range(1, n):
        new_children[new_parent[i]].append(i)
    order = [0]
    for u in order:
        for v in new_children[u]:
            order.append(v)
    sz = [1] * n
    for u in reversed(order):
        if u != 0:
            sz[new_parent[u]] += sz[u]
    return sz


findSubtreeSizes = solve


class Solution:
    def findSubtreeSizes(self, parent, s: str):
        return solve(parent, s)
