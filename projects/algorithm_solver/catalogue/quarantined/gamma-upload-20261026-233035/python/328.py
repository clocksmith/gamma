"""328. Odd Even Linked List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(head: ListNode | None) -> ListNode | None:
    if head is None:
        return None
    odd = head
    even = even_head = head.next
    while even is not None and even.next is not None:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head

class Solution:
    def oddEvenList(self, head):
        return solve(head)
