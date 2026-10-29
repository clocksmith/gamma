"""Hack2Hire 69bc55661cbff60a929be333 (Limit Tree Height by Deletions, variant 2) over an INFERRED spec; qualification unknown."""


def solve(root, maxHeight):
    order, stack = [], [root]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(node['children'])
    height = {}
    deletions = 0
    for node in reversed(order):
        h = 1 + max((height[child['id']] for child in node['children']), default=0)
        height[node['id']] = h
        if node is not root and h >= maxHeight:
            deletions += 1
    return deletions


class Solution:
    def minDeletionsForHeight(self, root, maxHeight):
        return solve(root, maxHeight)
