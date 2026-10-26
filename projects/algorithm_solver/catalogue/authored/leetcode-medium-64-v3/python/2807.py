"""2807. Insert Greatest Common Divisors in Linked List: insert between original adjacent nodes."""
from __future__ import annotations
from math import gcd


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n log M) time/O(1) auxiliary space; insert new gcd nodes, retain originals."""
    current = head
    while current is not None and current.next is not None:
        following = current.next
        current.next = ListNode(gcd(current.val, following.val), following)
        current = following
    return head


class Solution:
    def insertGreatestCommonDivisors(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
