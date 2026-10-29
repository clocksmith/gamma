"""Original frontend 1474 variant; qualification unknown."""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def _delete_nodes(head, m: int, n: int):
    cur = head
    while cur is not None:
        for _ in range(1, m):
            if cur is None:
                return head
            cur = cur.next
        if cur is None:
            break
        nxt = cur.next
        for _ in range(n):
            if nxt is None:
                break
            nxt = nxt.next
        cur.next = nxt
        cur = nxt
    return head


def solve(head, m: int, n: int):
    if isinstance(head, list):
        if not head:
            return []
        nodes = [ListNode(v) for v in head]
        for i in range(len(nodes) - 1):
            nodes[i].next = nodes[i + 1]
        cur = _delete_nodes(nodes[0], m, n)
        out = []
        while cur is not None:
            out.append(cur.val)
            cur = cur.next
        return out
    return _delete_nodes(head, m, n)


deleteNodes = solve


class Solution:
    def deleteNodes(self, head, m: int, n: int):
        return solve(head, m, n)
