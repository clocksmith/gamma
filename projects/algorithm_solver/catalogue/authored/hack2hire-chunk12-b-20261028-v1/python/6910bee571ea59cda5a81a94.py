"""Hack2Hire 6910bee571ea59cda5a81a94 (Minimum Root-to-Leaf Path Sum) over an INFERRED spec; qualification unknown."""


def solve(root):
    if not root:
        return []
    values, left, right = [root[0]], [-1], [-1]
    head, i = 0, 1
    while i < len(root):
        node = head
        head += 1
        if root[i] is not None:
            values.append(root[i]); left.append(-1); right.append(-1)
            left[node] = len(values) - 1
        i += 1
        if i < len(root):
            if root[i] is not None:
                values.append(root[i]); left.append(-1); right.append(-1)
                right[node] = len(values) - 1
            i += 1
    parent = [-1] * len(values)
    total = [0] * len(values)
    total[0] = values[0]
    best = -1
    stack = [0]
    while stack:
        node = stack.pop()
        if left[node] == -1 and right[node] == -1:
            if best == -1 or total[node] < total[best]:
                best = node
            continue
        for child in (right[node], left[node]):
            if child != -1:
                parent[child] = node
                total[child] = total[node] + values[child]
                stack.append(child)
    path = []
    while best != -1:
        path.append(values[best])
        best = parent[best]
    path.reverse()
    return path


class Solution:
    def minPathSum(self, root):
        return solve(root)
