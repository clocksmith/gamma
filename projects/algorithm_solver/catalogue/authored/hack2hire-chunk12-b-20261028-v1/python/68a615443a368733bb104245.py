"""Hack2Hire 68a615443a368733bb104245 (N-ary Tree Leaf Node Removal) over an INFERRED spec; qualification unknown."""


def solve(root):
    if not root:
        return []
    values, parent = [root[0]], [-1]
    head, i = 0, 2
    while i < len(root):
        p = head
        head += 1
        while i < len(root) and root[i] is not None:
            values.append(root[i]); parent.append(p)
            i += 1
        i += 1
    height = [0] * len(values)
    for v in range(len(values) - 1, 0, -1):
        if height[v] + 1 > height[parent[v]]:
            height[parent[v]] = height[v] + 1
    days = [[] for _ in range(height[0] + 1)]
    for v, h in enumerate(height):
        days[h].append(values[v])
    for day in days:
        day.sort()
    return days


class Solution:
    def removeLeavesByDay(self, root):
        return solve(root)
