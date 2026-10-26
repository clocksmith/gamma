"""2074. Reverse Nodes in Even Length Groups: copy values into fresh nodes using each actual group length."""
from __future__ import annotations


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n) time and O(n) auxiliary space excluding the returned list; inputs are read-only."""
    values = []
    current = head
    while current is not None:
        values.append(current.val)
        current = current.next
    dummy = ListNode()
    tail = dummy
    left = 0
    requested = 1
    while left < len(values):
        right = min(len(values), left + requested)
        indices = range(right - 1, left - 1, -1) if (right - left) % 2 == 0 else range(left, right)
        for index in indices:
            tail.next = ListNode(values[index])
            tail = tail.next
        left = right
        requested += 1
    return dummy.next


class Solution:
    def reverseEvenLengthGroups(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
