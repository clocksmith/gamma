"""Hack2Hire 6a7ce081d713d873ca7ac76a (Delete a Forest Subtree, variant 1) over an INFERRED spec; qualification unknown."""


def solve(parentIndex, node):
    n = len(parentIndex)
    children = [[] for _ in range(n)]
    for child, parent in enumerate(parentIndex):
        if child != parent:
            children[parent].append(child)
    result = list(parentIndex)
    stack = [node]
    result[node] = -1
    while stack:
        current = stack.pop()
        for child in children[current]:
            result[child] = -1
            stack.append(child)
    return result


class Solution:
    def deleteSubtree(self, parentIndex, node):
        return solve(parentIndex, node)
