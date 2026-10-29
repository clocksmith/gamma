"""Hack2Hire 69bc554c1cbff60a929be332 (Limit Tree Height by Deletions, variant 1) over an INFERRED spec; qualification unknown."""


def solve(root, deletedIds):
    deleted = set(deletedIds)
    best = 0
    stack = [(root, 1)]
    while stack:
        node, kept = stack.pop()
        if kept > best:
            best = kept
        for child in node['children']:
            stack.append((child, kept + (0 if child['id'] in deleted else 1)))
    return best


class Solution:
    def maxHeightAfterDeletion(self, root, deletedIds):
        return solve(root, deletedIds)
