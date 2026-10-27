"""203. Remove Linked List Elements."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(head: ListNode | None, val: int) -> ListNode | None:
    dummy = ListNode(0, head)
    current = dummy
    while current.next is not None:
        if current.next.val == val:
            current.next = current.next.next
        else:
            current = current.next
    return dummy.next

class Solution:
    def removeElements(self, head, val):
        return solve(head, val)
