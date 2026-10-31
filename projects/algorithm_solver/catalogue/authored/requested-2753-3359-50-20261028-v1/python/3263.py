"""Original frontend 3263 variant; qualification unknown."""


def solve(head):
    if isinstance(head, list):
        return list(head)
    out = []
    cur = head
    while cur is not None:
        out.append(cur.val)
        cur = cur.next
    return out


toArray = solve


class Solution:
    def toArray(self, head):
        return solve(head)
