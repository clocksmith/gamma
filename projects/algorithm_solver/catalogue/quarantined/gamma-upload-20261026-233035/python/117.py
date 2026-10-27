"""117. Populating Next Right Pointers in Each Node II."""
from __future__ import annotations

class Node:
    def __init__(self, val: int = 0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next

def solve(root: Node | None) -> Node | None:
    current = root
    while current is not None:
        dummy = Node()
        tail = dummy
        while current is not None:
            if current.left is not None:
                tail.next = current.left
                tail = tail.next
            if current.right is not None:
                tail.next = current.right
                tail = tail.next
            current = current.next
        current = dummy.next
    return root

class Solution:
    def connect(self, root):
        return solve(root)
