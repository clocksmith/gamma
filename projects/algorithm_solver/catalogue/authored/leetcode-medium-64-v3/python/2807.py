"""2807. Insert Greatest Common Divisors in Linked List: build a fresh list with each adjacent-pair gcd inserted."""
from __future__ import annotations
from math import gcd


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n log M) time and O(1) auxiliary space excluding returned nodes; inputs are read-only."""
    dummy = ListNode()
    tail = dummy
    current = head
    while current is not None:
        tail.next = ListNode(current.val)
        tail = tail.next
        if current.next is not None:
            tail.next = ListNode(gcd(current.val, current.next.val))
            tail = tail.next
        current = current.next
    return dummy.next


class Solution:
    def insertGreatestCommonDivisors(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
