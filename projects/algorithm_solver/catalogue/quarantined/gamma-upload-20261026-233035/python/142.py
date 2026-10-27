"""142. Linked List Cycle II."""
from __future__ import annotations

class ListNode:
    def __init__(self, x: int, next=None):
        self.val = x
        self.next = next

def solve(head: ListNode | None) -> ListNode | None:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            current = head
            while current is not slow:
                current = current.next
                slow = slow.next
            return current
    return None

class Solution:
    def detectCycle(self, head):
        return solve(head)
