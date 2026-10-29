"""Hack2Hire 68dc2e1c9736cfa4e906240c (Level With Maximum Nodes in an N-ary Tree) over an INFERRED spec; qualification unknown."""


def _parse(root):
    """Values and child-index lists of a LeetCode N-ary level-order list; nodes are numbered breadth-first."""
    if not root:
        return [], []
    vals, kids = [root[0]], [[]]
    q, i, n = 0, 2, len(root)
    while i < n:
        group = kids[q]
        while i < n and root[i] is not None:
            group.append(len(vals))
            vals.append(root[i])
            kids.append([])
            i += 1
        i += 1
        q += 1
    return vals, kids


def solve(root):
    vals, kids = _parse(root)
    if not vals:
        return 0
    level = [0] * len(vals)
    level[0] = 1
    counts = [0, 0]
    for v in range(len(vals)):  # breadth-first numbering: parents come before children
        counts[level[v]] += 1
        for c in kids[v]:
            level[c] = level[v] + 1
        if kids[v] and len(counts) <= level[v] + 1:
            counts.append(0)
    best, answer = 0, 0
    for lv in range(1, len(counts)):
        if counts[lv] > best:
            best, answer = counts[lv], lv
    return answer


class Solution:
    def levelWithMaxNodes(self, root):
        return solve(root)
