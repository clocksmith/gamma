"""Hack2Hire 68d849afae12841706c1fc74 (Min Root-to-Leaf Path Sum of N-ary Tree) over an INFERRED spec; qualification unknown."""


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
    total = list(vals)
    best = None
    for v in range(len(vals)):  # breadth-first numbering: a parent's total is final before its children
        if kids[v]:
            for c in kids[v]:
                total[c] = total[v] + vals[c]
        elif best is None or total[v] < best:
            best = total[v]
    return best


class Solution:
    def minPathSum(self, root):
        return solve(root)
