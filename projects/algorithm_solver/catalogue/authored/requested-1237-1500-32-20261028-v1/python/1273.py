"""Original frontend 1273 variant; qualification unknown."""


def solve(nodes: int, parent, value) -> int:
    children = [[] for _ in range(nodes)]
    for i in range(1, nodes):
        children[parent[i]].append(i)
    order = []
    stack = [0]
    while stack:
        u = stack.pop()
        order.append(u)
        for v in children[u]:
            stack.append(v)
    sub_sum = list(value)
    sub_cnt = [1] * nodes
    for u in reversed(order):
        if sub_sum[u] == 0:
            sub_cnt[u] = 0
        elif parent[u] != -1:
            p = parent[u]
            sub_sum[p] += sub_sum[u]
            sub_cnt[p] += sub_cnt[u]
    return sub_cnt[0]


deleteTreeNodes = solve


class Solution:
    def deleteTreeNodes(self, nodes: int, parent, value) -> int:
        return solve(nodes, parent, value)
