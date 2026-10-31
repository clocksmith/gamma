"""Original frontend 3294 variant; qualification unknown."""


def solve(node):
    if isinstance(node, list):
        return list(node)
    cur = node
    while cur is not None and getattr(cur, "prev", None) is not None:
        cur = cur.prev
    out = []
    while cur is not None:
        out.append(cur.val)
        cur = cur.next
    return out


toArray = solve


class Solution:
    def toArray(self, node):
        return solve(node)
