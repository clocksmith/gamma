"""2487. Remove Nodes From Linked List: keep a decreasing stack of values and build an independent result list."""
from __future__ import annotations


class ListNode:
    def __init__(self, val: int = 0, next: ListNode | None = None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    values = []
    node = head
    while node is not None:
        while values and values[-1] < node.val:
            values.pop()
        values.append(node.val)
        node = node.next
    result = None
    for value in reversed(values):
        result = ListNode(value, result)
    return result


class Solution:
    def removeNodes(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
