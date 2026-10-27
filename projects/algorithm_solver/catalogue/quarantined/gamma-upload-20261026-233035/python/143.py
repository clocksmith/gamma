"""143. Reorder List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(head: ListNode | None) -> None:
    if head is None or head.next is None:
        return
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    current = slow.next
    slow.next = None
    previous = None
    while current is not None:
        following = current.next
        current.next = previous
        previous = current
        current = following
    first, second = head, previous
    while second is not None:
        first_next, second_next = first.next, second.next
        first.next = second
        second.next = first_next
        first, second = first_next, second_next

class Solution:
    def reorderList(self, head) -> None:
        solve(head)
