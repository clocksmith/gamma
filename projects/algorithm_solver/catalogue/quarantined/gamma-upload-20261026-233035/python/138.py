"""138. Copy List with Random Pointer."""
from __future__ import annotations

class Node:
    def __init__(self, x: int, next=None, random=None):
        self.val = x
        self.next = next
        self.random = random

def solve(head: Node | None) -> Node | None:
    current = head
    while current is not None:
        current.next = Node(current.val, current.next)
        current = current.next.next
    current = head
    while current is not None:
        copy = current.next
        copy.random = current.random.next if current.random is not None else None
        current = copy.next
    dummy = Node(0)
    tail = dummy
    current = head
    while current is not None:
        copy = current.next
        current.next = copy.next
        tail.next = copy
        tail = copy
        current = current.next
    return dummy.next

class Solution:
    def copyRandomList(self, head):
        return solve(head)
