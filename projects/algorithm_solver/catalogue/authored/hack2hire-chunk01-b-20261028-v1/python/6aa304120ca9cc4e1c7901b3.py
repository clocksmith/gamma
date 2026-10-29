"""Hack2Hire 6aa304120ca9cc4e1c7901b3 (Directory Encryption Optimization, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(root):
    order, stack = [], [root]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(node['directories'])
    cost = {}
    for node in reversed(order):
        keep_off = keep_on = 0
        for f in node['files']:
            if f['isEncrypted']:
                keep_off += 1
            else:
                keep_on += 1
        for child in node['directories']:
            off, on = cost.pop(id(child))
            keep_off += off
            keep_on += on
        cost[id(node)] = (min(keep_off, 1 + keep_on), min(keep_on, 1 + keep_off))
    return cost[id(root)][0]


class Solution:
    def minStateOperations(self, root):
        return solve(root)
