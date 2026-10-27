"""116. Populating Next Right Pointers in Each Node."""
from __future__ import annotations

class Node:
    def __init__(self, val: int = 0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next

def solve(root: Node | None) -> Node | None:
    leftmost = root
    while leftmost is not None and leftmost.left is not None:
        current = leftmost
        while current is not None:
            current.left.next = current.right
            if current.next is not None:
                current.right.next = current.next.left
            current = current.next
        leftmost = leftmost.left
    return root

class Solution:
    def connect(self, root):
        return solve(root)
