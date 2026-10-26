"""2074. Reverse Nodes in Even Length Groups: relink original nodes by actual group length."""
from __future__ import annotations


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n) time/O(1) auxiliary space; relink original nodes in even groups."""
    dummy = ListNode(0, head)
    previous = dummy
    current = head
    requested = 1
    while current is not None:
        following = last = current
        count = 0
        while following is not None and count < requested:
            last = following
            following = following.next
            count += 1
        if count % 2 == 0:
            tail = current
            reversed_head = following
            for _ in range(count):
                next_node = current.next
                current.next = reversed_head
                reversed_head = current
                current = next_node
            previous.next = reversed_head
            previous = tail
        else:
            previous = last
        current = following
        requested += 1
    return dummy.next


class Solution:
    def reverseEvenLengthGroups(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
