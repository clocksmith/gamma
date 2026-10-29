"""Original frontend 328 variant; qualification unknown."""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def _relink(head):
    if head is None or head.next is None:
        return head
    odd = head
    even = head.next
    even_head = even
    while even is not None and even.next is not None:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


def solve(head):
    if isinstance(head, list):
        if not head:
            return []
        nodes = [ListNode(v) for v in head]
        for i in range(len(nodes) - 1):
            nodes[i].next = nodes[i + 1]
        cur = _relink(nodes[0])
        out = []
        while cur is not None:
            out.append(cur.val)
            cur = cur.next
        return out
    return _relink(head)


oddEvenList = solve


class Solution:
    def oddEvenList(self, head):
        return solve(head)
