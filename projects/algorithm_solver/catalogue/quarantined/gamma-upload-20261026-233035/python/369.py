"""369. Plus One Linked List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(head: ListNode | None) -> ListNode | None:
    dummy = ListNode(0, head)
    last_not_nine = dummy
    current = head
    while current is not None:
        if current.val != 9:
            last_not_nine = current
        current = current.next
    last_not_nine.val += 1
    current = last_not_nine.next
    while current is not None:
        current.val = 0
        current = current.next
    return dummy if dummy.val else dummy.next

class Solution:
    def plusOne(self, head):
        return solve(head)
