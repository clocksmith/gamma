"""141. Linked List Cycle."""
from __future__ import annotations

class ListNode:
    def __init__(self, x: int, next=None):
        self.val = x
        self.next = next

def solve(head: ListNode | None) -> bool:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False

class Solution:
    def hasCycle(self, head):
        return solve(head)
