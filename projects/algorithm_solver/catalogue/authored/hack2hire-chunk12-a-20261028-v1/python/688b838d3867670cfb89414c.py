"""Hack2Hire 688b838d3867670cfb89414c (Merge N-ary Tree) over an INFERRED spec; qualification unknown."""


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


def solve(root1, root2):
    v1, k1 = _parse(root1)
    v2, k2 = _parse(root2)
    if not v1 and not v2:
        return []
    out = []
    pairs = [(0 if v1 else -1, 0 if v2 else -1)]
    a, b = pairs[0]
    out.append((v1[a] if a >= 0 else 0) + (v2[b] if b >= 0 else 0))
    out.append(None)
    head = 0
    while head < len(pairs):
        a, b = pairs[head]
        head += 1
        ka = k1[a] if a >= 0 else ()
        kb = k2[b] if b >= 0 else ()
        for idx in range(max(len(ka), len(kb))):
            ca = ka[idx] if idx < len(ka) else -1
            cb = kb[idx] if idx < len(kb) else -1
            out.append((v1[ca] if ca >= 0 else 0) + (v2[cb] if cb >= 0 else 0))
            pairs.append((ca, cb))
        out.append(None)
    while out[-1] is None:
        out.pop()
    return out


class Solution:
    def mergeTrees(self, root1, root2):
        return solve(root1, root2)
