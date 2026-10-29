"""Original Hack2Hire 6987a577fedd959e9aa444e4 variant over an INFERRED specification; qualification unknown."""


def solve(parent, input):
    n = len(parent)
    children = [[] for _ in range(n)]
    for node in range(1, n):
        children[parent[node]].append(node)
    order = [0]
    for node in order:
        order.extend(children[node])
    subtree = list(input)
    for node in reversed(order):
        if node:
            subtree[parent[node]] += subtree[node]
    total = subtree[0]
    return min(abs(total - 2 * subtree[node]) for node in range(1, n))


class Solution:
    def minDrainageSplitDifference(self, parent, input):
        return solve(parent, input)
