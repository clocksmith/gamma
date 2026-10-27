"""147. Insertion Sort List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(head: ListNode | None) -> ListNode | None:
    dummy = ListNode()
    current = head
    while current is not None:
        following = current.next
        previous = dummy
        while previous.next is not None and previous.next.val <= current.val:
            previous = previous.next
        current.next = previous.next
        previous.next = current
        current = following
    return dummy.next

class Solution:
    def insertionSortList(self, head):
        return solve(head)
