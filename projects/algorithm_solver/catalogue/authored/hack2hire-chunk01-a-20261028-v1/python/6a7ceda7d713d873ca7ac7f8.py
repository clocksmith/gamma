"""Hack2Hire 6a7ceda7d713d873ca7ac7f8 (Delete a Forest Subtree, variant 2) over an INFERRED spec; qualification unknown."""


def solve(parentIndex, nodes):
    n = len(parentIndex)
    children = [[] for _ in range(n)]
    for child, parent in enumerate(parentIndex):
        if child != parent:
            children[parent].append(child)
    result = list(parentIndex)
    for node in nodes:
        if result[node] == -1:
            continue  # already deleted, together with its whole subtree
        result[node] = -1
        stack = [node]
        while stack:
            current = stack.pop()
            for child in children[current]:
                if result[child] != -1:
                    result[child] = -1
                    stack.append(child)
    return result


class Solution:
    def deleteSubtrees(self, parentIndex, nodes):
        return solve(parentIndex, nodes)
